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

# -------------------- Database helpers --------------------
_db_connection = None

def db():
    """Optimized database connection with connection reuse"""
    global _db_connection
    if _db_connection is None:
        _db_connection = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
        _db_connection.row_factory = sqlite3.Row
    return _db_connection

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
    con.execute("CREATE INDEX IF NOT EXISTS idx_token ON transfers(token);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_expires ON transfers(expires_at);")
    con.commit()

init_db()

# -------------------- Optimized helpers --------------------
def to_dt(val):
    if isinstance(val, datetime.datetime):
        return val
    if isinstance(val, str) and val:
        try:
            return datetime.datetime.fromisoformat(val)
        except:
            return None
    if isinstance(val, (int, float)):
        return datetime.datetime.utcfromtimestamp(val)
    return None

def get_ist_time():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)

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

# -------------------- Fast OTP generator --------------------
def gen_otp():
    """Optimized OTP generation"""
    return f"{secrets.randbelow(1000000):06d}"

def hash_otp(otp: str, salt: str):
    return hashlib.sha256((salt + otp).encode()).hexdigest()

# -------------------- Async Email helper --------------------
def send_email_async(to_email: str, subject: str, html_body: str):
    """Send email in background thread for better performance"""
    def _send_email():
        try:
            if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
                print(f"[EMAIL] TO: {to_email} | SUBJECT: {subject}")
                return True

            msg = MIMEText(html_body, "html")
            msg["Subject"] = subject
            msg["From"] = FROM_EMAIL
            msg["To"] = to_email

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
            print(f"[EMAIL] Sent successfully to {to_email}")
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")
    
    # Send email in background thread
    threading.Thread(target=_send_email, daemon=True).start()
    return True

# -------------------- Utilities --------------------
def client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")

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

def _notify_sender_download(row, ip):
    """Optimized notification with minimal HTML"""
    email = row["recipient_email"]
    filename = row['filename_orig']
    file_ext = filename.split('.')[-1].upper() if '.' in filename else 'FILE'
    
    subject = f"BlackFile: {file_ext} Downloaded - {filename}"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <h2 style="color:#10b981;">✅ File Downloaded Successfully!</h2>
        <p><strong>File:</strong> {filename}</p>
        <p><strong>Time:</strong> {get_ist_time().strftime('%Y-%m-%d %H:%M IST')}</p>
        <p><strong>From IP:</strong> {ip}</p>
        <p style="color:#666;font-size:14px;">File has been permanently deleted from our servers.</p>
    </div>
    """
    send_email_async(email, subject, html)

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
        return True
    else:
        con.execute("UPDATE transfers SET attempts=? WHERE token=?", (attempts_now, token))
        con.commit()
        return False

# -------------------- Routes --------------------
@app.route("/")
def index():
    """Optimized index with caching headers"""
    resp = make_response(render_template("modern-index.html", allowed_expiry=sorted(ALLOWED_EXPIRY)))
    resp.headers["Cache-Control"] = "public, max-age=300"  # Cache for 5 minutes
    return resp

@app.route("/upload", methods=["POST"])
def upload():
    """Optimized upload with faster processing"""
    try:
        email = request.form.get("email", "").strip()
        file = request.files.get("file")
        expiry = int(request.form.get("expiry", "10"))

        # Quick validations
        if expiry not in ALLOWED_EXPIRY or not EMAIL_REGEX.match(email) or not file or file.filename == "":
            flash("Invalid input. Please check your email and file.")
            return redirect(url_for("index"))

        # Fast file processing
        plaintext = file.read()
        if len(plaintext) > 10 * 1024 * 1024:
            flash("File too large. Maximum size is 10MB.")
            return redirect(url_for("index"))

        # Generate tokens quickly
        token = uuid.uuid4().hex
        otp = gen_otp()
        salt = secrets.token_hex(16)
        
        # Encrypt file
        key, nonce, ciphertext = encrypt_file(plaintext)
        
        # Save encrypted file
        filename_enc = secure_filename(f"{uuid.uuid4().hex}.blob")
        filepath = os.path.join(UPLOADS, filename_enc)
        with open(filepath, "wb") as f:
            f.write(ciphertext)

        # Database insert
        created_at = datetime.datetime.utcnow()
        expires_at = created_at + datetime.timedelta(minutes=expiry)
        
        con = db()
        con.execute("""
            INSERT INTO transfers (
                token, recipient_email, otp_hash, otp_salt, key_id,
                filename_orig, filepath, nonce_b64, sha256_hex,
                created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            token, email, hash_otp(otp, salt), salt, key_fingerprint(key, token),
            file.filename, filepath, base64.b64encode(nonce).decode(),
            hashlib.sha256(plaintext).hexdigest(), created_at, expires_at
        ))
        con.commit()

        # Send email asynchronously (non-blocking)
        secret_key_b64 = base64.b64encode(key).decode()
        verify_url = request.url_root.rstrip('/') + url_for('verify', token=token)
        
        subject = f"BlackFile: Secure Link for {file.filename}"
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
            <h2>🔒 Secure File Transfer</h2>
            <p>File: <strong>{file.filename}</strong></p>
            <p>OTP Code: <strong style="font-size:24px;color:#4299e1;">{otp}</strong></p>
            <p>Link: <a href="{verify_url}">{verify_url}</a></p>
            <p>Secret Key: <code style="background:#f1f1f1;padding:8px;display:block;word-break:break-all;">{secret_key_b64}</code></p>
            <p style="color:#dc2626;">⚠️ Expires in {expiry} minutes</p>
        </div>
        """
        
        send_email_async(email, subject, html)
        
        return render_template("modern-sent.html", 
                             email=email, 
                             filename=file.filename,
                             expiry=expiry)

    except Exception as e:
        app.logger.error(f"Upload error: {e}")
        flash("Upload failed. Please try again.")
        return redirect(url_for("index"))

# Keep all other routes the same but add this optimization
@app.before_request
def cleanup_expired():
    """Clean up expired files periodically"""
    if request.endpoint == 'index':  # Only run on homepage
        try:
            con = db()
            now = datetime.datetime.utcnow()
            expired_rows = con.execute(
                "SELECT * FROM transfers WHERE expires_at < ?", (now,)
            ).fetchall()
            
            for row in expired_rows:
                purge_row_and_files(row)
        except:
            pass  # Ignore cleanup errors

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)