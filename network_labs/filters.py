from passlib.hash import sha512_crypt as sha512_crypt_hash

def sha512_crypt(password: str) -> str:
    """Jinja2 filter to hash a password using the sha512 algorithm.

    Args:
        password (str): The password to hash

    Returns:
        str: The hashed password plus salt
    """
    return sha512_crypt_hash.encrypt(password, rounds=5000)

__all__ = [
    "sha512_crypt",
]
