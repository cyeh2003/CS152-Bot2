from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import binascii

def encrypt(plain_text, key):
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plain_text.encode()) + padder.finalize()
    encryptor = cipher.encryptor()
    cipher_text = encryptor.update(padded_data) + encryptor.finalize()
    
    # Return the cipher text encoded as a hexadecimal string
    return binascii.hexlify(cipher_text).decode()


def decrypt(encrypted_text, key):
    encrypted_bytes = binascii.unhexlify(encrypted_text)
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plain_text = unpadder.update(padded_data) + unpadder.finalize()
    
    # Return the plain text
    return plain_text.decode()

