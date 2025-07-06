import pyotp
from cryptography.fernet import Fernet

# ---------------------------------------
# Remplace ici par ta clé Fernet (base64)
# Exemple : exportée depuis ta variable FERNET_KEY
FERNET_KEY = b"TaCleFernetIci=="
fernet = Fernet(FERNET_KEY)

# ---------------------------------------
# Remplace ici par le secret chiffré qu'on a stocké en base
# Exemple : tu l'as lu manuellement depuis ta base PostgreSQL
encrypted_secret = b"le_mfa_secret_chiffre_en_bytes"

# ---------------------------------------
# Déchiffre le secret
decrypted_secret = fernet.decrypt(encrypted_secret).decode()
print("MFA Secret déchiffré :", decrypted_secret)

# ---------------------------------------
# Génère le code 2FA actuel
totp = pyotp.TOTP(decrypted_secret, interval=30)
print("Code TOTP actuel :", totp.now())
