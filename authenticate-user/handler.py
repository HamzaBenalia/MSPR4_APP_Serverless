import os
import json
import psycopg2
import time
from cryptography.fernet import Fernet

FERNET_KEY = os.environ.get('FERNET_KEY')
if not FERNET_KEY:
    raise ValueError("FERNET_KEY environment variable not set")
fernet = Fernet(FERNET_KEY.encode())

def handle(event, context=None):
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }

    method = getattr(context, 'http_method', 'POST').upper()
    print(f"[LOG] HTTP Method: {method}")

    if method == 'OPTIONS':
        print("[LOG] OPTIONS request - returning CORS headers only")
        return ("", 204, cors_headers)

    # Assure que c'est bien un POST
    if method != 'POST':
        body = json.dumps({"error": "Only POST method allowed"})
        print("[LOG] Method not allowed:", method)
        return (body, 405, {**cors_headers, 'Content-Type': 'application/json'})

    # Lecture et parsing du JSON envoyé
    print(f"[LOG] Raw event received: {event}")

    try:
        if isinstance(event, bytes):
            event = event.decode()
        data = json.loads(event)
        print(f"[LOG] Parsed JSON data: {data}")
    except Exception as e:
        body = json.dumps({"error": f"Invalid JSON format: {str(e)}"})
        print("[ERROR] JSON parsing failed:", e)
        return (body, 400, {**cors_headers, 'Content-Type': 'application/json'})

    username = data.get("username", "").strip()
    password = data.get("password", "")
    twofa_code = data.get("2fa_code", "")

    print(f"[LOG] username: '{username}', password: '{password}', 2fa_code: '{twofa_code}'")

    if not username or not password or not twofa_code:
        body = json.dumps({"error": "Missing username, password or 2fa_code"})
        print("[ERROR] Missing one or more required fields")
        return (body, 400, {**cors_headers, 'Content-Type': 'application/json'})

    # Connexion à la base de données
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
    POSTGRES_DB = os.environ.get('POSTGRES_DB')
    POSTGRES_USER = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')

    if not all([POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]):
        body = json.dumps({"error": "PostgreSQL environment variables not set"})
        print("[ERROR] PostgreSQL env vars missing")
        return (body, 500, {**cors_headers, 'Content-Type': 'application/json'})

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()
        # Exemple : récupérer mot de passe stocké pour vérifier
        cur.execute("SELECT password, mfa_secret FROM users WHERE username = %s", (username,))
        user_row = cur.fetchone()
        if user_row is None:
            body = json.dumps({"error": "Utilisateur non trouvé"})
            print("[ERROR] User not found in DB")
            cur.close()
            conn.close()
            return (body, 404, {**cors_headers, 'Content-Type': 'application/json'})

        stored_encrypted_password, stored_encrypted_secret = user_row

        # Décrypter mot de passe stocké
        stored_password = fernet.decrypt(stored_encrypted_password.encode()).decode()
        if stored_password != password:
            body = json.dumps({"error": "Mot de passe incorrect"})
            print("[ERROR] Password incorrect")
            cur.close()
            conn.close()
            return (body, 401, {**cors_headers, 'Content-Type': 'application/json'})

        # Vérifier code 2FA ici avec pyotp si tu veux (exemple non inclus)

        # Si OK, renvoyer succès
        body = json.dumps({"message": "Authentification réussie"})
        print("[LOG] Auth successful")

        cur.close()
        conn.close()

        return (body, 200, {**cors_headers, 'Content-Type': 'application/json'})

    except Exception as e:
        body = json.dumps({"error": str(e)})
        print("[ERROR] Exception during DB operation:", e)
        return (body, 500, {**cors_headers, 'Content-Type': 'application/json'})
