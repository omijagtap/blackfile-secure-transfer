# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

BlackFile is a secure file transfer web application built with Flask that allows users to send encrypted files via email links with OTP verification. Files are encrypted at rest using AES-GCM and automatically deleted after download or expiration.

## Development Commands

### Environment Setup
```powershell
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables (copy .env.example if needed)
# Ensure .env contains: APP_SECRET, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL
```

### Running the Application
```powershell
# Development server
python app.py

# Production server (using gunicorn)
gunicorn app:app
```

### Database Operations
```powershell
# Database is automatically initialized on first run
# SQLite database file: blackfile.db
# To reset database, simply delete blackfile.db and restart the app

# View database schema or data
sqlite3 blackfile.db
```

### Testing Email Functionality
```powershell
# Test email sending (standalone)
python send_email.py

# In development, emails are printed to console if SMTP credentials are not configured
```

## Architecture Overview

### Core Application Structure
- **`app.py`**: Main Flask application with all routes, database operations, and security logic
- **`send_email.py`**: Standalone email testing utility
- **`templates/`**: Jinja2 HTML templates for the web interface
- **`uploads/`**: Directory for encrypted file storage (temporary)
- **`.env`**: Environment configuration (not in version control)

### Security Architecture

**File Encryption**: Files are encrypted using AES-GCM with randomly generated 256-bit keys before storage. The encryption key is never stored server-side.

**Transfer Flow**:
1. File upload → AES-GCM encryption → SQLite metadata storage
2. Email sent with download link + OTP
3. Secret key displayed once to sender (base64-encoded)
4. Recipient needs both OTP + Secret key to decrypt and download
5. File automatically deleted after successful download

**Security Features**:
- OTP rate limiting (configurable max attempts before lockout)
- Time-based expiration (5, 10, or 60 minutes)
- HMAC-based key fingerprinting for validation
- IP tracking for download notifications
- Secure session handling for one-time secret display

### Database Schema

**`transfers` table**:
- `token`: Unique download identifier (UUID)
- `recipient_email`: Email address for delivery
- `otp_hash`/`otp_salt`: Hashed OTP for verification
- `key_id`: HMAC fingerprint of encryption key
- `filename_orig`: Original filename
- `filepath`: Encrypted file storage path
- `nonce_b64`: Base64-encoded encryption nonce
- `sha256_hex`: File integrity hash
- `created_at`/`expires_at`: Timestamp management
- `used`/`attempts`/`locked_until`: Security state tracking

### Key Application Flow

1. **Upload Route** (`/upload`): Validates file, encrypts content, stores metadata, sends email, displays secret key once
2. **Verify Route** (`/verify/<token>`): Validates OTP + secret key, decrypts file, serves download, notifies sender, deletes file
3. **Sent Route** (`/sent/<token>`): One-time display of secret key and transfer details

### Environment Configuration

Required `.env` variables:
- `APP_SECRET`: Flask session secret
- `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASS`: Email delivery
- `FROM_EMAIL`: Sender email address
- `OTP_MAX_TRIES`: Failed attempt limit (default: 3)
- `LOCK_MIN`: Lockout duration in minutes (default: 10)

### File Management

- Uploaded files are stored as encrypted `.blob` files in `uploads/`
- Files are automatically purged on download, expiration, or error
- SQLite database tracks all transfer metadata and state
- Maximum file size: 10MB (configurable via `MAX_CONTENT_LENGTH`)

### Email Templates

The application sends HTML-formatted emails with:
- Transfer details and expiration time (in IST timezone)
- Download link with embedded token
- OTP for verification
- Download confirmation notifications to sender

## Development Notes

- Database initialization happens automatically on app startup
- Time operations use UTC internally, IST for display
- File encryption uses cryptographically secure random keys and nonces
- All user inputs are validated and sanitized
- Error handling includes automatic cleanup of orphaned files
- Session-based secret key display ensures one-time access