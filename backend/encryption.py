"""
RAYR MONEY - CRYPTOGRAPHIC SECURE VAULT
Author: Senior Full-Stack Quantitative Architect
Description: Implements industry-grade symmetric cryptography using Fernet keys
             to ensure API keys are encrypted at rest and never exposed.
"""

import os
from cryptography.fernet import Fernet

class SecureVault:
    def __init__(self):
        # Read key from server environment or fallback to runtime generated secret
        self.secret_key = os.getenv("CRYPTOGRAPHY_SECRET_KEY")
        if not self.secret_key:
            self.secret_key = Fernet.generate_key().decode()
            
        self.cipher = Fernet(self.secret_key.encode())

    def encrypt_credential(self, raw_value: str) -> str:
        """Encrypts sensitive plain-text values into encrypted strings."""
        if not raw_value:
            return ""
        return self.cipher.encrypt(raw_value.encode()).decode()

    def decrypt_credential(self, encrypted_value: str) -> str:
        """Decrypts symmetric-cipher string payloads back to clean plain-text."""
        if not encrypted_value:
            return ""
        return self.cipher.decrypt(encrypted_value.encode()).decode()
