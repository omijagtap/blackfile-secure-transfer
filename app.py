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
    # Generate a more secure 6-digit OTP with better randomness
    import time
    # Use current timestamp as part of seed for uniqueness
    timestamp_seed = int(time.time() * 1000000) % 1000000
    # Combine with secure random for better uniqueness
    secure_part = secrets.randbelow(1000000)
    # XOR for better distribution and ensure 6 digits
    otp_num = (timestamp_seed ^ secure_part) % 1000000
    # Ensure it's always 6 digits (pad with leading zeros if needed)
    return f"{otp_num:06d}"

def hash_otp(otp: str, salt: str):
    return hashlib.sha256((salt + otp).encode()).hexdigest()

# -------------------- Email helper --------------------
def send_email(to_email: str, subject: str, html_body: str):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
        print("=== DEV EMAIL DUMP ===")
        print("TO:", to_email)
        print("SUBJECT:", subject)
        print("BODY:\n", html_body)
        print("======================")
        return True

    msg = MIMEText(html_body, "html")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    return True

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
    
    # Get file extension for subject
    file_ext = filename.split('.')[-1].upper() if '.' in filename else 'FILE'
    
    subject = f"BlackFile: {file_ext} File '{filename}' Was Downloaded Successfully"
    html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 20px; border-radius: 10px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #10b981; margin-bottom: 10px;">✅ Download Successful!</h2>
                <p style="color: #666; font-size: 16px;">Your secure file transfer has been completed</p>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981; margin: 20px 0;">
                <h3 style="color: #333; margin-top: 0;">📁 File Downloaded: <span style="color: #4299e1;">{filename}</span></h3>
                <div style="margin: 15px 0;">
                    <p style="margin: 8px 0;"><strong>🕒 Download Time:</strong> {get_ist_time().strftime('%Y-%m-%d at %H:%M IST')}</p>
                    <p style="margin: 8px 0;"><strong>🌐 Downloaded From:</strong> <code style="background: #f1f1f1; padding: 2px 6px; border-radius: 4px;">{ip}</code></p>
                </div>
            </div>
            
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; color: #856404;">
                    <strong>🔒 Security Notice:</strong> For your protection, this file has been permanently deleted from our servers and the download link is now invalid.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px;">
                <h3 style="color: white; margin: 0 0 10px 0;">🏠 Returning to Homepage</h3>
                <p style="color: #e0e7ff; margin: 0; font-size: 14px;">This notification will redirect you to the BlackFile homepage in 5 seconds...</p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
            <p style="color: #888; font-size: 12px; text-align: center; margin: 0;">
                This is an automated message from <strong>BlackFile</strong> secure transfer service.<br>
                <a href="#" style="color: #4299e1; text-decoration: none;">blackfile.secure</a>
            </p>
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
    resp.headers["Cache-Control"] = "no-store"
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
        
        html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">BlackFile Secure Transfer</h2>
                <p>You've received a secure file transfer via BlackFile.</p>
                
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Transfer Details:</strong></p>
                    <p>📁 File: <b>{filename_orig}</b></p>
                    <p>⏰ Expires: <b>{ist_expires_at.strftime('%Y-%m-%d at %H:%M IST')}</b></p>
                </div>
                
                <div style="background-color: #e8f4fc; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>To download your file:</strong></p>
                    <p>1. Visit: <a href="{link}" style="word-break: break-all;">{link}</a></p>
                    <p>2. Enter this OTP: <code style="background: #eee; padding: 5px; border-radius: 3px;">{otp}</code></p>
                    <p>3. Ask the sender for the <b>Secret Key</b> (shared separately)</p>
                </div>
                
                <p style="color: #d32f2f; font-size: 14px;">
                    ⚠️ For security, this link will expire after download or at the expiration time.
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #888; font-size: 12px;">
                    This is an automated message from BlackFile secure transfer service.</p>
            </div>
        """
        send_email(email, "Your BlackFile secure link", html)

        secret_key_b64 = base64.urlsafe_b64encode(secret_key).decode().rstrip("=")
        session[f"secret_{token}"] = secret_key_b64
        return redirect(url_for("sent", token=token))
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        flash("An error occurred during file upload. Please try again.")
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