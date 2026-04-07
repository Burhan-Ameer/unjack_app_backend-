from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError

password_hasher = PasswordHasher()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHash):
        return False

def get_password_hash(password: str) -> str:
    return password_hasher.hash(password)