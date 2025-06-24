from cryptography.fernet import Fernet
import os

# Récupérer la clé Fernet depuis une variable d'environnement (ou la coller en dur ici)
FERNET_KEY = os.environ.get('FERNET_KEY') or "DbpzAtPMWWZe7GPyLHQyN2Lm1fubdvtyNSgjiAHw1XY="

# Créer l'objet Fernet
fernet = Fernet(FERNET_KEY.encode())

# Texte à chiffrer
message = "Coucou, je teste ma clé Fernet !"

# Chiffrement
token = fernet.encrypt(message.encode())
print("Message chiffré :", token)

# Déchiffrement
decrypted = fernet.decrypt(token).decode()
print("Message déchiffré :", decrypted)

# Vérification simple
assert decrypted == message
print("Test OK, chiffrement/déchiffrement fonctionne.")
