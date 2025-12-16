import hashlib


def text_hash(text: str) -> str:
    """计算文本的 SHA-256 哈希

    参数:
        text: 输入文本
    返回:
        str: 16进制字符串形式的哈希值
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
