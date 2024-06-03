from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import binascii

def encrypt(plain_text, key):
    # Create a Cipher object
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    
    # Pad the plain text to be a multiple of the block size
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plain_text.encode()) + padder.finalize()
    
    # Encrypt the padded data
    encryptor = cipher.encryptor()
    cipher_text = encryptor.update(padded_data) + encryptor.finalize()
    
    # Return the cipher text encoded as a hexadecimal string
    return binascii.hexlify(cipher_text).decode()


def decrypt(encrypted_text, key):
    # Convert the hex string back to bytes
    encrypted_bytes = binascii.unhexlify(encrypted_text)
    
    # Create a Cipher object
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    
    # Decrypt the cipher text
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()
    
    # Unpad the decrypted data
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plain_text = unpadder.update(padded_data) + unpadder.finalize()
    
    # Return the plain text
    return plain_text.decode()

