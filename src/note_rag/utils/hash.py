import hashlib


def text_hash(text: str) -> str:
    # SHA-256 更安全
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
