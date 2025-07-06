import os
import base64
import qrcode
import io
import json
import time
import psycopg2
import pyotp
from cryptography.fernet import Fernet

FERNET_KEY = os.environ.get('FERNET_KEY')
if not FERNET_KEY:
    raise ValueError("FERNET_KEY environment variable not set")
fernet = Fernet(FERNET_KEY.encode())

def generate_qrcode(data):
    qr = qrcode.QRCode()
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def handle(event, context=None):
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }

    method = getattr(context, 'http_method', 'POST').upper()
    if method == 'OPTIONS':
        return ("", 204, cors_headers)

    POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
    POSTGRES_DB = os.environ.get('POSTGRES_DB')
    POSTGRES_USER = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')

    if not all([POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]):
        body = json.dumps({"error": "PostgreSQL environment variables not set"})
        return (body, 500, {**cors_headers, 'Content-Type': 'application/json'})

    # Récupération du username
    if isinstance(event, str):
        username = event.strip()
    elif isinstance(event, bytes):
        username = event.decode().strip()
    else:
        try:
            data = json.loads(event)
            username = data.get("username", "").strip()
        except Exception:
            username = str(event).strip()

    if not username:
        body = json.dumps({"error": "No username provided"})
        return (body, 400, {**cors_headers, 'Content-Type': 'application/json'})

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()

        # Vérifie que l'utilisateur existe et a un mot de passe
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        if row is None or row[0] is None:
            body = json.dumps({"error": "Utilisateur inconnu ou mot de passe non défini, créez d'abord un mot de passe"})
            cur.close()
            conn.close()
            return (body, 404, {**cors_headers, 'Content-Type': 'application/json'})

        # Génération du secret 2FA
        secret = pyotp.random_base32()
        encrypted_secret = fernet.encrypt(secret.encode()).decode()
        gen_date = int(time.time())

        # Mise à jour du secret 2FA en base
        cur.execute("""
            UPDATE users
            SET mfa_secret = %s,
                gen_date = %s
            WHERE username = %s
        """, (encrypted_secret, gen_date, username))
        conn.commit()
        cur.close()
        conn.close()

        # Génération du QR code avec le lien au format otpauth://
        otpauth_url = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="MonApp")
        qr_code_b64 = generate_qrcode(otpauth_url)

        body = json.dumps({"qr_code_base64": qr_code_b64, "otpauth_url": otpauth_url})
        return (body, 200, {**cors_headers, 'Content-Type': 'application/json'})

    except Exception as e:
        body = json.dumps({"error": str(e)})
        return (body, 500, {**cors_headers, 'Content-Type': 'application/json'})
