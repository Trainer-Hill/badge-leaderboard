"""PBKDF2-SHA256 password hashing for admin auth.

Kept dependency-free (stdlib only) and importable without booting Dash, so a
hash can be generated from the command line:

    PYTHONPATH=src python -m util.passwords 'the-password'

Prints a hash suitable for TH_BL_PASSWORD_HASH or a TH_BL_USERS entry.
"""
import base64
import hashlib
import hmac
import os

# Parameters for PBKDF2
HASH_NAME = "sha256"
ITERATIONS = 100_000
SALT_SIZE = 16  # bytes
KEY_LENGTH = 32  # bytes


def hash_password(password: str) -> str:
    salt = os.urandom(SALT_SIZE)
    key = hashlib.pbkdf2_hmac(HASH_NAME, password.encode(), salt, ITERATIONS, dklen=KEY_LENGTH)
    return base64.b64encode(salt + key).decode()  # Store both salt and key together


def verify_password(password: str, stored_hash: str) -> bool:
    decoded = base64.b64decode(stored_hash.encode())
    salt = decoded[:SALT_SIZE]
    original_key = decoded[SALT_SIZE:]
    new_key = hashlib.pbkdf2_hmac(HASH_NAME, password.encode(), salt, ITERATIONS, dklen=KEY_LENGTH)
    return hmac.compare_digest(new_key, original_key)


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("usage: python -m util.passwords '<password>'", file=sys.stderr)
        raise SystemExit(2)
    print(hash_password(sys.argv[1]))
