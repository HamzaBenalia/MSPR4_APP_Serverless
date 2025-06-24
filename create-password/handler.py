import os
import string
import random
import base64
import qrcode
import io
from cryptography.fernet import Fernet
import psycopg2
import time
import json

FERNET_KEY = os.environ.get('FERNET_KEY')
if not FERNET_KEY:
    raise ValueError("FERNET_KEY environment variable not set")
key = FERNET_KEY.encode()
fernet = Fernet(key)

def generate_password(length=24):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

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

    # Gestion de la méthode HTTP
    method = getattr(context, 'http_method', 'POST').upper()

    if method == 'OPTIONS':
        # Réponse aux préflight CORS
        return ("", 204, cors_headers)

    # POST : traitement principal
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
    POSTGRES_DB = os.environ.get('POSTGRES_DB')
    POSTGRES_USER = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')

    if not all([POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]):
        body = json.dumps({"error": "PostgreSQL environment variables not set"})
        return (body, 500, {**cors_headers, 'Content-Type': 'application/json'})

    # Récupération du username : 
    # Ici on suppose que le corps (event) est une chaîne simple, ex: "Hamza"
    if isinstance(event, str):
        username = event.strip()
    elif isinstance(event, bytes):
        username = event.decode().strip()
    else:
        # Si c'est un dict JSON (par ex), on essaye de récupérer username
        try:
            data = json.loads(event)
            username = data.get("username", "").strip()
        except Exception:
            username = str(event).strip()

    if not username:
        body = json.dumps({"error": "No username provided"})
        return (body, 400, {**cors_headers, 'Content-Type': 'application/json'})

    password = generate_password()
    encrypted_password = fernet.encrypt(password.encode()).decode()

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()
        gen_date = int(time.time())

        cur.execute("""
            INSERT INTO users (username, password, gen_date, expired)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username) DO UPDATE
            SET password = EXCLUDED.password,
                gen_date = EXCLUDED.gen_date,
                expired = FALSE
            """,
            (username, encrypted_password, gen_date, False)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        body = json.dumps({"error": str(e)})
        return (body, 500, {**cors_headers, 'Content-Type': 'application/json'})

    qr_code_b64 = generate_qrcode(password)
    body = json.dumps({"qr_code_base64": qr_code_b64})
    return (body, 200, {**cors_headers, 'Content-Type': 'application/json'})
