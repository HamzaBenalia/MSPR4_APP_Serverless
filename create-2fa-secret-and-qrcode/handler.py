import base64
import io
import os
import psycopg2
from cryptography.fernet import Fernet
import pyotp
import qrcode
from datetime import datetime

def handle(req):
    username = req.strip()

    if not username:
        return "Username required", 400

    # 🔐 Charger la clé de chiffrement (même que celle utilisée dans la 3.1)
    key = os.environ.get("FERNET_KEY")
    if not key:
        return "Encryption key not configured", 500
    fernet = Fernet(key.encode())

    # 🔐 Générer un secret TOTP
    totp = pyotp.TOTP(pyotp.random_base32())
    secret = totp.secret

    # 📷 Générer le QR code (compatible Google Authenticator)
    otpauth_url = totp.provisioning_uri(name=username, issuer_name="OpenFaaS Demo")
    qr = qrcode.make(otpauth_url)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()

    # 🔒 Chiffrer le secret
    encrypted_secret = fernet.encrypt(secret.encode()).decode()

    # 🗄️ Stocker le secret en base
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST"),
            database=os.environ.get("POSTGRES_DB"),
            user=os.environ.get("POSTGRES_USER"),
            password=os.environ.get("POSTGRES_PASSWORD")
        )
        cur = conn.cursor()
        cur.execute("UPDATE users SET mfa_secret = %s WHERE username = %s", (encrypted_secret, username))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return f"Database error: {e}", 500

    return qr_base64
