import os
import stat
import logging
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet

logger = logging.getLogger("ai_workforce_os.security.vault")

KEY_FILE_PATH = Path.home() / ".ai_workforce_vault.key"

class VaultProvider:
    """
    Cryptographic secrets vault provider.
    Uses authenticated symmetric AES-128-CBC + HMAC-SHA256 (Fernet).
    Key is protected with restrictive 0600 POSIX permissions.
    """
    def __init__(self, key_path: Path = KEY_FILE_PATH):
        self.key_path = key_path
        self._fernet: Optional[Fernet] = None
        self._init_key()

    def _init_key(self):
        # 1. Check environment variable override
        env_key = os.getenv("AI_WORKFORCE_VAULT_KEY")
        if env_key:
            self._fernet = Fernet(env_key.encode("utf-8"))
            return

        # 2. Check local key file
        if self.key_path.exists():
            with open(self.key_path, "rb") as f:
                key = f.read().strip()
            self._fernet = Fernet(key)
        else:
            # Generate new key and protect with 0600 permissions
            key = Fernet.generate_key()
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_path, "wb") as f:
                f.write(key)
            self.key_path.chmod(stat.S_IRUSR | stat.S_IWUSR) # 0600
            self._fernet = Fernet(key)
            logger.info(f"Initialized new secure vault master key at {self.key_path} with 0600 permissions.")

    def encrypt(self, plaintext: str) -> str:
        """Encrypts a plaintext secret into an authenticated ciphertext string."""
        if not plaintext:
            return ""
        if not self._fernet:
            self._init_key()
        encrypted_bytes = self._fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypts ciphertext string back to plaintext secret."""
        if not ciphertext:
            return ""
        if not self._fernet:
            self._init_key()
        decrypted_bytes = self._fernet.decrypt(ciphertext.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")

    def verify_master_auth(self, candidate_key: str) -> bool:
        """Validates an owner master key attempt for sensitive operations."""
        if not candidate_key:
            return False
        with open(self.key_path, "rb") as f:
            actual_key = f.read().strip().decode("utf-8")
        return candidate_key.strip() == actual_key
