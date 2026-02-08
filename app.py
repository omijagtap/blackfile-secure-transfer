import os
import re
import sqlite3
import uuid
import secrets
import hashlib
import base64
import datetime
import hmac
import smtplib
import threading
from email.mime.text import MIMEText
from io import BytesIO

from flask import (
    Flask, render_template, request, redirect,
    url_for, send_file, abort, flash, session, make_response
)
from werkzeug.utils import secure_filename
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -------------------- App & Config --------------------
app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET", "dev-secret-change-me")

# Limits & folders
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
ROOT = os.path.dirname(__file__)
UPLOADS = os.path.join(ROOT, "uploads")
os.makedirs(UPLOADS, exist_ok=True)
DB_PATH = os.path.join(ROOT, "blackfile.db")

# Email settings
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USER or "no-reply@example.com")

# Security settings
ALLOWED_EXPIRY = {5, 10, 60}
OTP_MAX_TRIES = int(os.environ.get("OTP_MAX_TRIES", "3"))
LOCK_MIN = int(os.environ.get("LOCK_MIN", "10"))
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# -------------------- AI Security Features --------------------

def get_ai_security_tip(filename):
    """
    AI-powered security tip generator based on file type analysis
    Returns personalized security advice for different file types
    """
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    tips = {
        # Documents
        'pdf': {
            'icon': '📄',
            'tip': 'PDFs may contain metadata like author name and edit history. Consider using a PDF cleaner before sharing sensitive documents.',
            'risk': 'medium'
        },
        'doc': {
            'icon': '📝',
            'tip': 'Word documents may contain tracked changes and comments. Use "Accept All Changes" and remove comments before sharing.',
            'risk': 'medium'
        },
        'docx': {
            'icon': '📝',
            'tip': 'Word documents may contain tracked changes and comments. Use "Accept All Changes" and remove comments before sharing.',
            'risk': 'medium'
        },
        'xls': {
            'icon': '📊',
            'tip': 'Excel files may contain hidden sheets and formulas. Review all sheets before sharing.',
            'risk': 'medium'
        },
        'xlsx': {
            'icon': '📊',
            'tip': 'Excel files may contain hidden sheets and formulas. Review all sheets before sharing.',
            'risk': 'medium'
        },
        
        # Images
        'jpg': {
            'icon': '📸',
            'tip': 'Images may contain EXIF data including GPS location, camera model, and timestamp. Remove metadata if sharing sensitive photos.',
            'risk': 'low'
        },
        'jpeg': {
            'icon': '📸',
            'tip': 'Images may contain EXIF data including GPS location, camera model, and timestamp. Remove metadata if sharing sensitive photos.',
            'risk': 'low'
        },
        'png': {
            'icon': '🖼️',
            'tip': 'PNG files may contain embedded text and metadata. Verify content before sharing.',
            'risk': 'low'
        },
        'gif': {
            'icon': '🎬',
            'tip': 'Animated images are safe to share but may contain multiple frames. Preview before sending.',
            'risk': 'low'
        },
        
        # Executables (High Risk)
        'exe': {
            'icon': '⚠️',
            'tip': 'Executable files pose security risks. Only share with trusted recipients who expect this file type.',
            'risk': 'high'
        },
        'bat': {
            'icon': '⚠️',
            'tip': 'Batch script files can execute commands. Ensure recipient knows this is a legitimate file.',
            'risk': 'high'
        },
        'cmd': {
            'icon': '⚠️',
            'tip': 'Command script files can execute system commands. Share only with trusted recipients.',
            'risk': 'high'
        },
        'sh': {
            'icon': '⚠️',
            'tip': 'Shell scripts can execute commands. Verify recipient expects this file type.',
            'risk': 'high'
        },
        
        # Archives
        'zip': {
            'icon': '📦',
            'tip': 'Compressed files may contain multiple items. Verify all contents are safe and expected before sharing.',
            'risk': 'medium'
        },
        'rar': {
            'icon': '📦',
            'tip': 'Compressed files may contain multiple items. Verify all contents are safe and expected before sharing.',
            'risk': 'medium'
        },
        '7z': {
            'icon': '📦',
            'tip': 'Compressed files may contain multiple items. Verify all contents are safe and expected before sharing.',
            'risk': 'medium'
        },
        
        # Text files
        'txt': {
            'icon': '📃',
            'tip': 'Text files are generally safe. Ensure no sensitive information is included in plain text.',
            'risk': 'low'
        },
        'csv': {
            'icon': '📋',
            'tip': 'CSV files may contain sensitive data. Review contents before sharing.',
            'risk': 'low'
        }
    }
    
    # Default tip for unknown file types
    default_tip = {
        'icon': '🔒',
        'tip': 'Always verify the recipient email address before sending sensitive files. Double-check for typos.',
        'risk': 'low'
    }
    
    return tips.get(ext, default_tip)


def ai_malware_scan(filename, file_bytes):
    """
    AI-powered malware detection system
    Performs multiple security checks on uploaded files
    Returns: (is_safe: bool, message: str, threat_level: str)
    """
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    file_size = len(file_bytes)
    
    # Check 1: Dangerous file extensions (High Risk)
    dangerous_extensions = ['exe', 'bat', 'cmd', 'scr', 'vbs', 'js', 'jar', 'com', 'pif', 'msi']
    if ext in dangerous_extensions:
        return False, f"⚠️ {ext.upper()} files are potentially dangerous and blocked for security. Use a secure file transfer method for executables.", "HIGH"
    
    # Check 2: File size anomaly detection
    if file_size < 100:  # Suspiciously small
        return False, "⚠️ File appears corrupted or empty. Upload blocked for security.", "MEDIUM"
    
    if file_size > 10 * 1024 * 1024:  # Over 10MB (should be caught by Flask, but double-check)
        return False, "⚠️ File exceeds maximum size limit of 10 MB.", "LOW"
    
    # Check 3: Suspicious file patterns (AI-based pattern matching)
    # Check for executable headers in non-executable files
    suspicious_patterns = [
        (b'MZ\x90\x00', 'PE executable header'),  # Windows executable
        (b'\x7fELF', 'ELF executable header'),    # Linux executable
        (b'!This program', 'Self-extracting archive'),
        (b'<script', 'Embedded script'),          # JavaScript in files
    ]
    
    # Only check first 2KB for performance
    file_header = file_bytes[:2048]
    
    for pattern, description in suspicious_patterns:
        if pattern in file_header:
            # Allow scripts in legitimate file types
            if ext in ['html', 'htm', 'xml'] and pattern == b'<script':
                continue
            return False, f"⚠️ File contains suspicious pattern ({description}). Upload blocked for security.", "HIGH"
    
    # Check 4: Double extension check (e.g., file.pdf.exe)
    if filename.count('.') > 1:
        parts = filename.split('.')
        if len(parts) > 2:
            # Check if any part before the last extension is suspicious
            for part in parts[:-1]:
                if part.lower() in dangerous_extensions:
                    return False, "⚠️ File has suspicious double extension. Upload blocked for security.", "HIGH"
    
    # Check 5: Null byte injection check (only in filename, not file content)
    # Note: Binary files like PDFs naturally contain null bytes in content
    if '\x00' in filename:
        return False, "⚠️ Filename contains null bytes. Upload blocked for security.", "HIGH"
    
    # All checks passed - file is safe
    return True, "✅ File passed AI security scan. Safe to upload.", "SAFE"


def get_file_risk_badge(risk_level):
    """
    Returns a visual badge for file risk level
    """
    badges = {
        'low': '🟢 Low Risk',
        'medium': '🟡 Medium Risk',
        'high': '🔴 High Risk',
        'SAFE': '✅ Verified Safe',
        'HIGH': '⛔ Blocked',
        'MEDIUM': '⚠️ Warning'
    }
    return badges.get(risk_level, '🔵 Unknown')

# -------------------- Database helpers --------------------
def db():
    con = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE,
            recipient_email TEXT,
            otp_hash TEXT,
            otp_salt TEXT,
            key_id TEXT,
            filename_orig TEXT,
            filepath TEXT,
            nonce_b64 TEXT,
            sha256_hex TEXT,
            created_at TIMESTAMP,
            expires_at TIMESTAMP,
            used INTEGER DEFAULT 0,
            attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP NULL,
            downloaded_from_ip TEXT NULL
        );
    """)
    # Add indexes for faster queries
    con.execute("CREATE INDEX IF NOT EXISTS idx_token ON transfers(token);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_expires ON transfers(expires_at);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_used ON transfers(used);")
    con.commit()
    con.close()

init_db()

# -------------------- Time helpers --------------------
def to_dt(val):
    if isinstance(val, datetime.datetime):
        return val
    if isinstance(val, str) and val:
        return datetime.datetime.fromisoformat(val)
    if isinstance(val, (int, float)):
        return datetime.datetime.utcfromtimestamp(val)
    return None

def get_ist_time():
    utc_now = datetime.datetime.utcnow()
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    ist_now = utc_now + ist_offset
    return ist_now

# -------------------- Crypto helpers --------------------
def encrypt_file(plaintext_bytes: bytes):
    key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)
    return key, nonce, ciphertext

def decrypt_file(key: bytes, nonce: bytes, ciphertext: bytes):
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)

def key_fingerprint(secret_key_bytes: bytes, token: str) -> str:
    mac = hmac.new(app.secret_key.encode(), secret_key_bytes + token.encode(), hashlib.sha256).hexdigest()
    return mac[:32]

# -------------------- OTP helpers --------------------
def gen_otp():
    """Fast and secure 6-digit OTP generation"""
    return f"{secrets.randbelow(1000000):06d}"

def hash_otp(otp: str, salt: str):
    return hashlib.sha256((salt + otp).encode()).hexdigest()

# -------------------- Synchronous Email Helper (Fixed for Debugging) --------------------
def send_email(to_email: str, subject: str, html_body: str):
    """Send email synchronously - errors will be raised to the caller"""
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
        print(f"[EMAIL MOCK] TO: {to_email} | SUBJECT: {subject[:50]}...")
        return True

    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    # Connect to SMTP server (Support both SSL and TLS)
    try:
        print(f"[EMAIL] Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        if int(SMTP_PORT) == 465:
            print("[EMAIL] Mode: SSL (Secure)")
            # SSL Connection (Standard for 465)
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as s:
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
        else:
            print("[EMAIL] Mode: TLS (StartTLS)")
            # TLS Connection (Standard for 587)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
    except Exception as e:
        print(f"[EMAIL] ❌ Failed to connect: {e}")
        raise e  # Re-raise to show error in UI
    
    print(f"[EMAIL] ✅ Sent to {to_email}")
    return True

# Alias for compatibility if needed
def send_email_async(to_email: str, subject: str, html_body: str):
    return send_email(to_email, subject, html_body)

# -------------------- Utilities --------------------
def client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "")

def is_expired(row):
    expires_at = to_dt(row["expires_at"])
    if not expires_at:
        return True
    return datetime.datetime.utcnow() >= expires_at

def purge_row_and_files(row):
    try:
        if row["filepath"]:
            os.remove(row["filepath"])
    except FileNotFoundError:
        pass
    con = db()
    con.execute("DELETE FROM transfers WHERE token=?", (row["token"],))
    con.commit()
    con.close()

def _notify_sender_download(row, ip):
    email = row["recipient_email"]
    filename = row['filename_orig']
    
    subject = f"BlackFile: File '{filename}' Downloaded"
    html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 560px; margin: 0 auto; background: #ffffff; color: #1f2937;">
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 24px; text-align: center;">
                <h1 style="margin: 0; font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">Download Successful</h1>
                <p style="margin: 8px 0 0 0; font-size: 13px; color: rgba(255,255,255,0.9);">Your file has been downloaded</p>
            </div>
            
            <div style="padding: 32px 24px;">
                <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 20px; margin-bottom: 24px;">
                    <p style="margin: 0 0 12px 0; font-size: 12px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Download Details</p>
                    <p style="margin: 0 0 8px 0; font-size: 14px; color: #374151;"><strong>File:</strong> {filename}</p>
                    <p style="margin: 0 0 8px 0; font-size: 14px; color: #374151;"><strong>Time:</strong> {get_ist_time().strftime('%Y-%m-%d at %H:%M IST')}</p>
                    <p style="margin: 0; font-size: 14px; color: #374151;"><strong>IP Address:</strong> <code style="background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 13px;">{ip}</code></p>
                </div>
                
                <div style="background: #fef3c7; border: 1px solid #fde68a; border-radius: 6px; padding: 16px;">
                    <p style="margin: 0; font-size: 12px; color: #92400e; line-height: 1.6;"><strong>🔒 Security Notice:</strong> The file has been permanently deleted from our servers and the download link is now invalid.</p>
                </div>
            </div>
            
            <div style="background: #f9fafb; padding: 20px 24px; border-top: 1px solid #e5e7eb; text-align: center;">
                <p style="margin: 0; font-size: 11px; color: #6b7280;">This is an automated message from <strong>BlackFile</strong> secure transfer service</p>
            </div>
        </div>
    """
    send_email(email, subject, html)

def _bump_attempts_and_maybe_lock(token: str, attempts_now: int):
    attempts_now = (attempts_now or 0) + 1
    con = db()
    if attempts_now >= OTP_MAX_TRIES:
        locked_until = datetime.datetime.utcnow() + datetime.timedelta(minutes=LOCK_MIN)
        con.execute(
            "UPDATE transfers SET attempts=?, locked_until=? WHERE token=?",
            (attempts_now, locked_until, token)
        )
        con.commit()
        con.close()
        return True
    else:
        con.execute("UPDATE transfers SET attempts=? WHERE token=?", (attempts_now, token))
        con.commit()
        con.close()
        return False

# -------------------- Routes --------------------
@app.route("/")
def index():
    resp = make_response(render_template("modern-index.html", allowed_expiry=sorted(ALLOWED_EXPIRY)))
    # Cache static content for better performance
    resp.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
    return resp

@app.route("/upload", methods=["POST"])
def upload():
    try:
        email = request.form.get("email", "").strip()
        file = request.files.get("file")
        expiry = int(request.form.get("expiry", "10"))

        if expiry not in ALLOWED_EXPIRY:
            flash("Invalid expiry option.")
            return redirect(url_for("index"))

        if not EMAIL_REGEX.match(email):
            flash("Please enter a valid email address.")
            return redirect(url_for("index"))

        if not file or file.filename == "":
             flash("Please choose a file.")
             return redirect(url_for("index"))
            
        if not file.content_type:
            flash("Invalid file type.")
            return redirect(url_for("index"))

        filename_orig = secure_filename(file.filename)
        file_bytes = file.read()
        if not file_bytes:
            flash("Uploaded file is empty.")
            return redirect(url_for("index"))

        # ✨ AI SECURITY CHECK: Malware Detection
        is_safe, scan_message, threat_level = ai_malware_scan(filename_orig, file_bytes)
        if not is_safe:
            app.logger.warning(f"AI Malware Scan blocked file: {filename_orig} - {scan_message}")
            flash(scan_message, "error")
            return redirect(url_for("index"))
        
        # ✨ AI FEATURE: Get personalized security tip
        security_tip = get_ai_security_tip(filename_orig)
        app.logger.info(f"AI Security Scan: {filename_orig} - {scan_message}")

        sha256_hex = hashlib.sha256(file_bytes).hexdigest()

        # Encrypt file at rest
        secret_key, nonce, ciphertext = encrypt_file(file_bytes)
        token = uuid.uuid4().hex
        blob_path = os.path.join(UPLOADS, f"{token}.blob")

        with open(blob_path, "wb") as f:
            f.write(ciphertext)

        # OTP + key ID
        otp = gen_otp()
        salt = uuid.uuid4().hex
        otp_hash = hash_otp(otp, salt)
        k_id = key_fingerprint(secret_key, token)

        now = datetime.datetime.utcnow()
        expires_at = now + datetime.timedelta(minutes=expiry)

        con = db()
        con.execute("""
            INSERT INTO transfers (
                id, token, recipient_email, otp_hash, otp_salt, key_id,
                filename_orig, filepath, nonce_b64, sha256_hex, created_at, expires_at
            ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            token, email, otp_hash, salt, k_id,
            filename_orig, blob_path, base64.b64encode(nonce).decode(),
            sha256_hex, now, expires_at
        ))
        con.commit()
        con.close()

        link = request.url_root.rstrip("/") + url_for("verify", token=token)
        
        # Convert UTC expires_at to IST for email display
        ist_expires_at = expires_at + datetime.timedelta(hours=5, minutes=30)
        
        # Store secret key in session for the sent page (in case user wants to see it)
        secret_key_b64 = base64.urlsafe_b64encode(secret_key).decode().rstrip("=")
        session[f"secret_{token}"] = secret_key_b64
        
        html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 560px; margin: 0 auto; background: #ffffff; color: #1f2937;">
                <div style="background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%); padding: 24px; text-align: center;">
                    <h1 style="margin: 0; font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">BlackFile Secure Transfer</h1>
                    <p style="margin: 8px 0 0 0; font-size: 13px; color: rgba(255,255,255,0.9);">You have received a secure file</p>
                </div>
                
                <div style="padding: 32px 24px;">
                    <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 20px; margin-bottom: 24px;">
                        <p style="margin: 0 0 12px 0; font-size: 12px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">Transfer Details</p>
                        <p style="margin: 0 0 8px 0; font-size: 14px; color: #374151;"><strong>File:</strong> {filename_orig}</p>
                        <p style="margin: 0; font-size: 14px; color: #374151;"><strong>Expires:</strong> {ist_expires_at.strftime('%Y-%m-%d at %H:%M IST')}</p>
                    </div>
                    
                    <div style="background: #eff6ff; border: 1px solid #dbeafe; border-radius: 6px; padding: 20px; margin-bottom: 24px;">
                        <p style="margin: 0 0 12px 0; font-size: 12px; font-weight: 600; color: #1e40af; text-transform: uppercase; letter-spacing: 0.5px;">Download Instructions</p>
                        <ol style="margin: 0; padding-left: 20px; font-size: 13px; color: #374151; line-height: 1.8;">
                            <li style="margin-bottom: 8px;">Click the link below to access the download page</li>
                            <li style="margin-bottom: 8px;">Enter this OTP code: <code style="background: #dbeafe; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 14px; font-weight: 600; color: #1e40af;">{otp}</code></li>
                            <li>Enter this Secret Key: <code style="background: #dbeafe; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 12px; font-weight: 600; color: #1e40af;">{secret_key_b64}</code></li>
                        </ol>
                    </div>
                    
                    <div style="text-align: center; margin-bottom: 24px;">
                        <a href="{link}" style="display: inline-block; background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 6px; font-size: 14px; font-weight: 600; letter-spacing: 0.3px;">Download File</a>
                    </div>
                    
                    <div style="background: #fef3c7; border: 1px solid #fde68a; border-radius: 6px; padding: 16px; margin-bottom: 24px;">
                        <p style="margin: 0; font-size: 12px; color: #92400e; line-height: 1.6;"><strong>⚠️ Security Notice:</strong> This link expires after one download or at the expiration time. The file will be permanently deleted from our servers.</p>
                    </div>
                </div>
                
                <div style="background: #f9fafb; padding: 20px 24px; border-top: 1px solid #e5e7eb; text-align: center;">
                    <p style="margin: 0; font-size: 11px; color: #6b7280;">This is an automated message from <strong>BlackFile</strong> secure transfer service</p>
                </div>
            </div>
        """
        send_email(email, "Your BlackFile secure link", html)

        # Redirect to index with success message including AI security tip
        success_msg = f"✅ File sent successfully to {email}! {security_tip['icon']} AI Tip: {security_tip['tip']}"
        flash(success_msg, "success")
        return redirect(url_for("index"))
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        # SHOW REAL ERROR TO USER FOR DEBUGGING
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for("index"))

@app.route("/sent/<token>")
def sent(token):
    secret = session.pop(f"secret_{token}", None)
    if secret is None:
        flash("This confirmation page is viewable only once.")
        return redirect(url_for("index"))

    con = db()
    row = con.execute("SELECT * FROM transfers WHERE token=?", (token,)).fetchone()
    con.close()
    if not row:
        abort(404)

    created_at = to_dt(row["created_at"]) or datetime.datetime.utcnow()
    expires_at = to_dt(row["expires_at"]) or (created_at + datetime.timedelta(minutes=10))
    expiry_minutes = max(1, int((expires_at - created_at).total_seconds() // 60))

    return render_template(
        "modern-sent.html",
        link=request.url_root.rstrip("/") + url_for("verify", token=token),
        email=row["recipient_email"],
        secret_key=secret,
        sha256_hex=row["sha256_hex"],
        expiry_minutes=expiry_minutes
    )

@app.route("/verify/<token>", methods=["GET", "POST"])
def verify(token):
    con = db()
    row = con.execute("SELECT * FROM transfers WHERE token=?", (token,)).fetchone()
    con.close()

    if not row:
        abort(404)

    if is_expired(row):
        purge_row_and_files(row)
        return render_template("modern-verify.html", token=token, expired=True)

    if row["used"]:
        return render_template("modern-verify.html", token=token, already_erased=True)

    locked_until = row["locked_until"]
    if locked_until:
        lu = to_dt(locked_until)
        now = datetime.datetime.utcnow()
        if lu and now < lu:
            minutes_left = max(1, int((lu - now).total_seconds() // 60))
            return render_template("modern-verify.html", token=token, locked=True, minutes_left=minutes_left)

    if request.method == "GET":
        # Format expires_at for JavaScript
        expires_at = to_dt(row["expires_at"])
        expires_at_iso = expires_at.isoformat() + 'Z' if expires_at else None
        
        resp = make_response(render_template(
            "modern-verify.html", 
            token=token, 
            expires_at=expires_at_iso,
            expires_at_raw=expires_at
        ))
        resp.headers["Cache-Control"] = "no-store"
        return resp

    otp_input = request.form.get("otp", "").strip().replace("-", "")  # Remove dash from OTP
    secret_key_b64 = request.form.get("secret_key", "").strip()

    if not otp_input or not secret_key_b64:
        expires_at = to_dt(row["expires_at"])
        expires_at_iso = expires_at.isoformat() + 'Z' if expires_at else None
        return render_template("modern-verify.html", token=token, error="Please enter both OTP and Secret Key.", expires_at=expires_at_iso)

    if hash_otp(otp_input, row["otp_salt"]) != row["otp_hash"]:
        was_locked = _bump_attempts_and_maybe_lock(token, row["attempts"])
        
        con = db()
        row2 = con.execute("SELECT * FROM transfers WHERE token=?", (token,)).fetchone()
        con.close()
        
        attempts_remaining = OTP_MAX_TRIES - row2["attempts"]
        
        if was_locked or (row2["locked_until"] and to_dt(row2["locked_until"]) > datetime.datetime.utcnow()):
            lu2 = to_dt(row2["locked_until"])
            minutes_left = max(1, int((lu2 - datetime.datetime.utcnow()).total_seconds() // 60))
            return render_template("modern-verify.html", token=token, locked=True, minutes_left=minutes_left)
        else:
            expires_at = to_dt(row["expires_at"])
            expires_at_iso = expires_at.isoformat() + 'Z' if expires_at else None
            return render_template("modern-verify.html", token=token, wrong_otp=True, 
                                  attempts_remaining=attempts_remaining, expires_at=expires_at_iso)

    try:
        pad = "=" * (-len(secret_key_b64) % 4)
        secret_key = base64.urlsafe_b64decode(secret_key_b64 + pad)
    except Exception:
        _bump_attempts_and_maybe_lock(token, row["attempts"])
        expires_at = to_dt(row["expires_at"])
        expires_at_iso = expires_at.isoformat() + 'Z' if expires_at else None
        return render_template("modern-verify.html", token=token, error="Invalid key format. Please paste the exact Secret Key.", expires_at=expires_at_iso)

    if key_fingerprint(secret_key, token) != row["key_id"]:
        _bump_attempts_and_maybe_lock(token, row["attempts"])
        expires_at = to_dt(row["expires_at"])
        expires_at_iso = expires_at.isoformat() + 'Z' if expires_at else None
        return render_template("modern-verify.html", token=token, wrong_secret=True, expires_at=expires_at_iso)

    try:
        with open(row["filepath"], "rb") as f:
            ciphertext = f.read()
    except FileNotFoundError:
        purge_row_and_files(row)
        return render_template("modern-verify.html", token=token, already_erased=True)

    try:
        nonce = base64.b64decode(row["nonce_b64"])
        plaintext = decrypt_file(secret_key, nonce, ciphertext)

        # Mark as downloaded in database
        con = db()
        con.execute("UPDATE transfers SET used=1, downloaded_from_ip=? WHERE token=?", (client_ip(), token))
        con.commit()
        con.close()

        # Send download notification
        _notify_sender_download(row, client_ip())

        # Encode file data for client-side download
        file_data_b64 = base64.b64encode(plaintext).decode()
        
        # Schedule cleanup - remove encrypted file from server
        try:
            os.remove(row["filepath"])
        except FileNotFoundError:
            pass

        # Return success page with auto-download and redirect
        return render_template(
            "download-success.html",
            filename=row["filename_orig"],
            file_data=file_data_b64,
            file_size=len(plaintext)
        )
    except Exception as e:
        app.logger.error(f"Decryption error: {e}")
        expires_at = to_dt(row["expires_at"])
        expires_at_iso = expires_at.isoformat() + 'Z' if expires_at else None
        return render_template("modern-verify.html", token=token, error="Decryption failed. Please check your Secret Key.", expires_at=expires_at_iso)

@app.errorhandler(404)
def not_found(e):
    return render_template("modern-404.html"), 404

@app.errorhandler(413)
def too_large(e):
    flash("File too large. Maximum size is 10MB.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)