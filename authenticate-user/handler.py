from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import psycopg2
import pyotp
import os

app = FastAPI()

fernet_key = os.environ["FERNET_KEY"].encode()
fernet = Fernet(fernet_key)

class AuthData(BaseModel):
    username: str
    password: str
    code_2fa: str

@app.post("/")
def handler(data: AuthData):
    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        port=os.environ["DB_PORT"]
    )
    cur = conn.cursor()

    cur.execute("SELECT password, gen_date, expired, mfa_secret FROM users WHERE username = %s", (data.username,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    enc_password, gen_date, expired, enc_mfa_secret = row

    if gen_date + timedelta(days=180) < datetime.utcnow():
        cur.execute("UPDATE users SET expired = TRUE WHERE username = %s", (data.username,))
        conn.commit()
        cur.close()
        conn.close()
        raise HTTPException(status_code=403, detail="Mot de passe expiré. Veuillez le régénérer.")

    if expired:
        raise HTTPException(status_code=403, detail="Compte expiré. Veuillez recréer votre mot de passe.")

    decrypted_password = fernet.decrypt(enc_password.encode()).decode()
    if data.password != decrypted_password:
        raise HTTPException(status_code=401, detail="Mot de passe invalide")

    decrypted_secret = fernet.decrypt(enc_mfa_secret.encode()).decode()
    totp = pyotp.TOTP(decrypted_secret)
    if not totp.verify(data.code_2fa):
        raise HTTPException(status_code=401, detail="Code 2FA invalide")

    cur.close()
    conn.close()

    return {"status": "success", "message": "Authentification réussie"}
