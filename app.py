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

import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


from flask import (
    Flask, render_template, request, redirect,
    url_for, send_file, abort, flash, session, make_response
)
from werkzeug.utils import secure_filename
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

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
ALLOWED_EXPIRY = {5, 10, 60}  # minutes
OTP_MAX_TRIES = int(os.environ.get("OTP_MAX_TRIES", "5"))
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
    return f"{secrets.randbelow(1000000):06d}"

def hash_otp(otp: str, salt: str):
    return hashlib.sha256((salt + otp).encode()).hexdigest()

# -------------------- Email helper --------------------
def send_email(to_email: str, subject: str, html_body: str):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
        # Dev mode: print instead of sending
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
    subject = "BlackFile: Your file was downloaded"
    html = f"""
        <p>Your file <b>{row['filename_orig']}</b> has been downloaded.</p>
        <p>From IP: <code>{ip}</code></p>
        <p>Token: <code>{row['token']}</code></p>
    """
    # Notify recipient (same email) — if you want sender email, store sender in DB and use that here.
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
    else:
        con.execute("UPDATE transfers SET attempts=? WHERE token=?", (attempts_now, token))
    con.commit()
    con.close()

# -------------------- Routes --------------------
@app.route("/")
def index():
    # Prevent caching of the form page
    resp = make_response(render_template("index.html", allowed_expiry=sorted(ALLOWED_EXPIRY)))
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.route("/upload", methods=["POST"])
def upload():
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

    # Persist transfer row
    con = db()
    con.execute("""
        INSERT INTO transfers (
            token, recipient_email, otp_hash, otp_salt, key_id,
            filename_orig, filepath, nonce_b64, sha256_hex, created_at, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        token, email, otp_hash, salt, k_id,
        filename_orig, blob_path, base64.b64encode(nonce).decode(),
        sha256_hex, now, expires_at
    ))
    con.commit()
    con.close()

    # Build and send email
    link = request.url_root.rstrip("/") + url_for("verify", token=token)
    html = f"""
        <h3>BlackFile download link</h3>
        <p>This link expires at <b>{expires_at.isoformat()}Z</b> and can be used once.</p>
        <p><b>Link:</b> <a href="{link}">{link}</a></p>
        <p><b>OTP:</b> <code>{otp}</code></p>
        <p>You'll also need the <b>Secret Key</b> shared by the sender via a separate channel.</p>
    """
    send_email(email, "Your BlackFile secure link", html)

    # Show secret to sender once
    secret_key_b64 = base64.urlsafe_b64encode(secret_key).decode().rstrip("=")
    session[f"secret_{token}"] = secret_key_b64
    return redirect(url_for("sent", token=token))

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
        "sent.html",
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

    # Link expired?
    if is_expired(row):
        purge_row_and_files(row)
        return render_template("verify.html", token=token, expired=True)

    # Already used?
    if row["used"]:
        return render_template("verify.html", token=token, already_erased=True)

    # Locked?
    locked_until = row["locked_until"]
    if locked_until:
        lu = to_dt(locked_until)
        now = datetime.datetime.utcnow()
        if lu and now < lu:
            minutes_left = max(1, int((lu - now).total_seconds() // 60))
            return render_template("verify.html", token=token, locked=True, minutes_left=minutes_left)

    if request.method == "GET":
        resp = make_response(render_template("verify.html", token=token))
        # avoid any caching for the verify page
        resp.headers["Cache-Control"] = "no-store"
        return resp

    # POST: validate OTP and secret key
    otp_input = request.form.get("otp", "").strip()
    secret_key_b64 = request.form.get("secret_key", "").strip()

    if not otp_input or not secret_key_b64:
        return render_template("verify.html", token=token, error="Please enter both OTP and Secret Key.")

    # OTP check
    if hash_otp(otp_input, row["otp_salt"]) != row["otp_hash"]:
        _bump_attempts_and_maybe_lock(token, row["attempts"])
        # Re-check lock status after increment
        con = db()
        row2 = con.execute("SELECT * FROM transfers WHERE token=?", (token,)).fetchone()
        con.close()
        locked = False
        minutes_left = None
        if row2 and row2["locked_until"]:
            lu2 = to_dt(row2["locked_until"])
            if lu2 and datetime.datetime.utcnow() < lu2:
                locked = True
                minutes_left = max(1, int((lu2 - datetime.datetime.utcnow()).total_seconds() // 60))
        return render_template("verify.html", token=token, wrong_otp=True, locked=locked, minutes_left=minutes_left)

    # Secret key decode + check
    try:
        pad = "=" * (-len(secret_key_b64) % 4)
        secret_key = base64.urlsafe_b64decode(secret_key_b64 + pad)
    except Exception:
        _bump_attempts_and_maybe_lock(token, row["attempts"])
        return render_template("verify.html", token=token, error="Invalid key format. Please paste the exact Secret Key.")

    if key_fingerprint(secret_key, token) != row["key_id"]:
        _bump_attempts_and_maybe_lock(token, row["attempts"])
        return render_template("verify.html", token=token, wrong_secret=True)

    # Load ciphertext
    try:
        with open(row["filepath"], "rb") as f:
            ciphertext = f.read()
    except FileNotFoundError:
        purge_row_and_files(row)
        return render_template("verify.html", token=token, already_erased=True)

    # Decrypt and send
    try:
        nonce = base64.b64decode(row["nonce_b64"])
        plaintext = decrypt_file(secret_key, nonce, ciphertext)

        file_stream = BytesIO(plaintext)
        file_stream.seek(0)

        ip = client_ip()
        con = db()
        con.execute("UPDATE transfers SET used=1, downloaded_from_ip=? WHERE token=?", (ip, token))
        con.commit()
        con.close()

        # Delete encrypted blob (single-use)
        try:
            os.remove(row["filepath"])
        except FileNotFoundError:
            pass

        _notify_sender_download(row, ip)
        # Return as attachment download
        return send_file(
            file_stream,
            as_attachment=True,
            download_name=row["filename_orig"],
            mimetype="application/octet-stream",
            max_age=0
        )

    except Exception as e:
        print("Decrypt/send error:", e)
        return render_template("verify.html", token=token, error="Decryption failed. Please check your inputs.",Success = True)

@app.route("/purge", methods=["POST"])
def purge():
    con = db()
    rows = con.execute("SELECT * FROM transfers").fetchall()
    con.close()
    purged = 0
    for r in rows:
        # purge expired OR used & file gone
        if is_expired(r) or (r["used"] and not os.path.exists(r["filepath"] or "")):
            purge_row_and_files(r)
            purged += 1
    flash(f"Purged {purged} expired/used transfers.")
    return redirect(url_for("index"))

@app.after_request
def add_security_headers(resp):
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Cache-Control"] = "no-store"
    # Keep CSS/JS external; allow data: images for emojis, etc.
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self'; "
        "script-src 'self'; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'"
    )
    return resp

@app.route("/health")
def health():
    return {"status": "ok"}

# -------------------- Run --------------------
if __name__ == "__main__":
    # Use 0.0.0.0 when deploying in a container
    app.run(debug=True, port=5000)
