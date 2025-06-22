from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os
import logging
from typing import Tuple

class AESEncryption:
    def __init__(self, key: bytes = None):
        self.key = key or self._load_or_generate_key()
        self.backend = default_backend()
        self.logger = logging.getLogger(__name__)
    
    def _load_or_generate_key(self) -> bytes:
        """Загрузка или генерация ключа шифрования"""
        key_file = os.getenv('ENCRYPTION_KEY_FILE', '.encryption_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                key = f.read()
                self.logger.info("Encryption key loaded")
                return key
        else:
            # Генерация нового ключа 256-bit
            key = os.urandom(32)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Только владелец может читать
            self.logger.info("New encryption key generated")
            return key
    
    def encrypt(self, plaintext: str) -> Tuple[bytes, bytes]:
        """Шифрование AES-256-CBC"""
        iv = os.urandom(16)  # 128 bits
        
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        return ciphertext, iv
    
    def decrypt(self, ciphertext: bytes, iv: bytes) -> str:
        """Расшифровка"""
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext.decode('utf-8')