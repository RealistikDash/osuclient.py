import hashlib
import string
import random

RAND_CHARS = string.ascii_letters + string.digits

def random_string(length: int) -> str:
    """Generates a random string of a given length."""
    return "".join(random.choice(RAND_CHARS) for _ in range(length))

def md5(data: str) -> str:
    """Generates an MD5 hash of a string."""
    return hashlib.md5(data.encode()).hexdigest()

def random_md5() -> str:
    """Generates a random valid MD5 hash."""
    return md5(random_string(16))
