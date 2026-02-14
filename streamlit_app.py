import streamlit as st
import os
import sqlite3
import uuid
import secrets
import hashlib
import base64
import datetime
import hmac
import re
from io import BytesIO
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Config & Setup ---
st.set_page_config(page_title="BlackFile Secure Transfer", page_icon="🔒", layout="centered")

# Ensure uploads directory exists
ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOADS = os.path.join(ROOT, "uploads")
os.makedirs(UPLOADS, exist_ok=True)
DB_PATH = os.path.join(ROOT, "blackfile_streamlit.db")

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "omijagtap304@gmail.com")
OTP_MAX_TRIES = 3
LOCK_MIN = 10

# Custom CSS for Premium Look
st.markdown("""
<style>
    .main {
        background-color: #000000;
        color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #d13a3a;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
    }
    .upload-container {
        border: 2px dashed #ff4b4b;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        background: rgba(255, 75, 75, 0.05);
    }
    .security-tip {
        background: rgba(30, 30, 30, 0.8);
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    h1, h2, h3 {
        color: #ff4b4b !format;
    }
</style>
""", unsafe_allow_html=True)

# --- AI Security Features ---
def get_ai_security_tip(filename):
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    tips = {
        'pdf': {'icon': '📄', 'tip': 'PDFs may contain metadata like author name. Consider cleaning before sharing.'},
        'docx': {'icon': '📝', 'tip': 'Word docs may contain tracked changes. Accept all changes before sharing.'},
        'xlsx': {'icon': '📊', 'tip': 'Excel files may contain hidden sheets. Review all sheets.'},
        'jpg': {'icon': '📸', 'tip': 'Images may contain GPS location EXIF data. Remove if sensitive.'},
        'zip': {'icon': '📦', 'tip': 'Verify all contents are safe before sharing compressed archives.'},
        'exe': {'icon': '⚠️', 'tip': 'Executables pose high risk. Only share with trusted recipients.'},
        'csv': {'icon': '📋', 'tip': 'CSV files may contain sensitive data. Review contents before sharing.'}
    }
    return tips.get(ext, {'icon': '🔒', 'tip': 'Always verify the recipient email address before sending.'})

def ai_malware_scan(filename, file_bytes):
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    dangerous = ['exe', 'bat', 'cmd', 'scr', 'vbs', 'js', 'jar', 'msi']
    if ext in dangerous:
        return False, f"⚠️ {ext.upper()} files are blocked for security.", "HIGH"
    if len(file_bytes) < 100:
        return False, "⚠️ File appears corrupted or empty.", "MEDIUM"
    
    suspicious_patterns = [b'MZ\x90\x00', b'\x7fELF', b'!This program']
    header = file_bytes[:2048]
    for pattern in suspicious_patterns:
        if pattern in header:
            return False, "⚠️ File contains executable headers. Blocked.", "HIGH"
    
    return True, "✅ File passed AI security scan.", "SAFE"

# --- Database helpers ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute("""
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
                locked_until TIMESTAMP NULL
            );
        """)
        conn.commit()

init_db()

# --- Crypto & Email ---
def encrypt_file(plaintext_bytes: bytes):
    key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)
    return key, nonce, ciphertext

def decrypt_file(ciphertext: bytes, key_bytes: bytes, nonce_bytes: bytes):
    aesgcm = AESGCM(key_bytes)
    return aesgcm.decrypt(nonce_bytes, ciphertext, None)

def send_otp_email(to_email, otp, download_url):
    if not SENDGRID_API_KEY:
        st.warning("⚠️ Email configuration missing. OTP is: " + otp)
        return False
    
    subject = "🔒 Secure File Transfer: Your Access Code"
    html_content = f"""
    <div style="font-family: sans-serif; padding: 20px; border: 1px solid #ff4b4b; border-radius: 10px;">
        <h2 style="color: #ff4b4b;">BlackFile Secure Transfer</h2>
        <p>Someone has sent you a secure file.</p>
        <p>Your one-time pass-code is:</p>
        <div style="font-size: 24px; font-weight: bold; color: #ff4b4b; margin: 20px 0;">{otp}</div>
        <p>Click the link below to access the download page:</p>
        <a href="{download_url}" style="background: #ff4b4b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Download Page</a>
        <p style="margin-top: 20px; font-size: 12px; color: #888;">This code and link will expire soon.</p>
    </div>
    """
    message = Mail(from_email=FROM_EMAIL, to_emails=to_email, subject=subject, html_content=html_content)
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# --- Main Logic ---
def main():
    st.title("🔒 BlackFile Secure Transfer")
    st.markdown("### AI-Powered Zero-Trust File Sharing")
    
    # Handle Download URL via query params
    # Updated to st.query_params for newer Streamlit versions
    query_params = st.query_params
    token = query_params.get("token")
    
    if token:
        show_download_interface(token)
    else:
        show_upload_interface()

def show_upload_interface():
    with st.container():
        st.subheader("📤 Send a Secure File")
        recipient_email = st.text_input("Recipient Email Address")
        expiry = st.selectbox("Link Expiry", [5, 10, 60], format_func=lambda x: f"{x} Minutes")
        
        uploaded_file = st.file_uploader("Choose a file to transfer (Max 10MB)", type=None)
        
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            
            # AI Scan
            is_safe, scan_msg, scan_level = ai_malware_scan(uploaded_file.name, file_bytes)
            st.info(scan_msg)
            
            # Security Tip
            tip_data = get_ai_security_tip(uploaded_file.name)
            st.markdown(f"""
            <div class="security-tip">
                <b>{tip_data['icon']} AI Security Tip:</b><br>{tip_data['tip']}
            </div>
            """, unsafe_allow_html=True)
            
            if not is_safe:
                st.error("Upload blocked by AI security scan.")
            elif st.button("Encrypt & Send Securely"):
                if not recipient_email or not re.match(r"[^@]+@[^@]+\.[^@]+", recipient_email):
                    st.error("Please enter a valid recipient email.")
                else:
                    process_upload(uploaded_file.name, file_bytes, recipient_email, expiry)

def process_upload(filename, file_bytes, email, expiry_min):
    with st.status("Encrypting and preparing transfer..."):
        # Encrypt
        key, nonce, ciphertext = encrypt_file(file_bytes)
        token = secrets.token_urlsafe(16)
        otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        salt = secrets.token_hex(8)
        otp_hash = hashlib.sha256((salt + otp).encode()).hexdigest()
        
        # Save ciphertext
        filepath = os.path.join(UPLOADS, f"{token}.enc")
        with open(filepath, "wb") as f:
            f.write(ciphertext)
            
        # DB Entry
        expires_at = datetime.datetime.now() + datetime.timedelta(minutes=expiry_min)
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO transfers (token, recipient_email, otp_hash, otp_salt, filename_orig, filepath, nonce_b64, sha256_hex, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                token, email, otp_hash, salt, filename, filepath, 
                base64.b64encode(nonce).decode(), 
                hashlib.sha256(file_bytes).hexdigest(),
                expires_at.isoformat()
            ))
            conn.commit()
        
        # Determine the base URL for the code
        # In Streamlit Cloud, it's the app URL
        app_url = st.secrets.get("APP_URL", "http://localhost:8501")
        download_url = f"{app_url}?token={token}"
        
        # Send Email
        success = send_otp_email(email, otp, download_url)
        
    if success:
        st.success(f"✅ File sent securely to {email}!")
        st.balloons()
        st.info("The recipient will receive an email with the access code and link.")
        st.warning(f"🗝️ SECRET KEY: {base64.b64encode(key).decode()}\n\nSHARE THIS KEY MANUALLY WITH THE RECIPIENT. Without this key, the file cannot be decrypted.")
    else:
        st.success(f"✅ Transfer prepared! Direct Link: {download_url}")
        st.write(f"OTP (Email failed): {otp}")
        st.warning(f"🗝️ SECRET KEY: {base64.b64encode(key).decode()}")

def show_download_interface(token):
    st.subheader("📥 Secure File Download")
    
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM transfers WHERE token = ? AND used = 0", (token,)).fetchone()
    
    if not row:
        st.error("This transfer link is invalid or has already been used.")
        if st.button("Go to Home"):
            st.query_params.clear()
            st.rerun()
        return

    # Check expiry
    expires_at = datetime.datetime.fromisoformat(row['expires_at'])
    if datetime.datetime.now() > expires_at:
        st.error("This transfer link has expired.")
        return

    st.info(f"You have been sent a secure file: **{row['filename_orig']}**")
    
    with st.form("download_form"):
        otp_input = st.text_input("Enter 6-Digit Access Code (from email)", max_chars=6)
        secret_key_input = st.text_input("Enter Secret Key (from sender)")
        submit = st.form_submit_button("Verify & Download")
        
    if submit:
        # Verify OTP
        input_hash = hashlib.sha256((row['otp_salt'] + otp_input).encode()).hexdigest()
        if input_hash != row['otp_hash']:
            st.error("Invalid access code.")
            return
            
        try:
            # Decrypt
            key_bytes = base64.b64decode(secret_key_input)
            nonce_bytes = base64.b64decode(row['nonce_b64'])
            
            with open(row['filepath'], "rb") as f:
                ciphertext = f.read()
                
            plaintext = decrypt_file(ciphertext, key_bytes, nonce_bytes)
            
            # Success
            st.success("Verification successful! Your file is ready.")
            st.download_button(
                label="Click here to download file",
                data=plaintext,
                file_name=row['filename_orig'],
                on_click=mark_used,
                args=(token, row['filepath'])
            )
            
        except Exception:
            st.error("Decryption failed. Please check your Secret Key.")

def mark_used(token, filepath):
    with get_db_connection() as conn:
        conn.execute("UPDATE transfers SET used = 1 WHERE token = ?", (token,))
        conn.commit()
    # Delete the file for security
    if os.path.exists(filepath):
        os.remove(filepath)

if __name__ == "__main__":
    main()
