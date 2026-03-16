import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from config import Config


class EncryptionService:
    """AES-256-GCM encryption for document storage."""

    def __init__(self):
        key_source = Config.ENCRYPTION_KEY.encode('utf-8')
        # Ensure key is exactly 32 bytes for AES-256
        self.key = key_source[:32].ljust(32, b'\0')

    def encrypt_file(self, file_data):
        """Encrypt file data using AES-256-GCM.
        
        Returns:
            tuple: (encrypted_data, nonce) both as bytes
        """
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        encrypted_data = aesgcm.encrypt(nonce, file_data, None)
        # Prepend nonce to encrypted data for storage
        return nonce + encrypted_data

    def decrypt_file(self, encrypted_data):
        """Decrypt file data.
        
        Args:
            encrypted_data: nonce (12 bytes) + ciphertext
            
        Returns:
            bytes: decrypted file data
        """
        aesgcm = AESGCM(self.key)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        return aesgcm.decrypt(nonce, ciphertext, None)

    def encrypt_file_to_disk(self, file_data, output_path):
        """Encrypt and save file to disk."""
        encrypted = self.encrypt_file(file_data)
        with open(output_path, 'wb') as f:
            f.write(encrypted)
        return output_path

    def decrypt_file_from_disk(self, input_path):
        """Read and decrypt file from disk."""
        with open(input_path, 'rb') as f:
            encrypted = f.read()
        return self.decrypt_file(encrypted)


# Singleton instance
encryption_service = EncryptionService()
