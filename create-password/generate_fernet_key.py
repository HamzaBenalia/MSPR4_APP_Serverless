from cryptography.fernet import Fernet

key = Fernet.generate_key()
print(key.decode())  # clé base64 en string
