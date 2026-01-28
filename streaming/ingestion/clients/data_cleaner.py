"""
Data Cleaner Module
Inspired by preprocess/preprocess_new.py logic
"""

import re

# Từ điển Teencode đầy đủ (từ preprocess_new.py)
TEENCODE_DICT = {
    "ko": "không",
    "k": "không",
    "kh": "không",
    "dc": "được",
    "đc": "được",
    "t": "tôi",
    "tao": "tôi",
    "nt": "nhắn tin",
    "fb": "facebook",
    "hnay": "hôm nay",
    "ng": "người",
    "mn": "mọi người",
    "ae": "anh em",
    "v": "vậy",
    "add": "thêm",
    "ib": "inbox",
    "fuck": "địt",
    "đm": "địt mẹ",
    "vcl": "vãi cả lồn",
    "dell": "đéo",
    "éo": "đéo",
    "clgt": "cái lồn gì thế",
    "vkl": "vãi cả lồn",
}


def clean_text_advanced(text):
    """
    Làm sạch text theo logic từ preprocess_new.py
    - Xóa URL, mentions, email
    - Xóa ký tự đặc biệt (giữ lại dấu câu cơ bản)
    - Chuyển teencode
    - Xóa ký tự lặp quá 2 lần
    """
    if not text or str(text) == "nan":
        return ""

    text = str(text).lower()

    # Xóa URL, email, mentions
    text = re.sub(r"http\S+|www\.\S+|\S+@\S+|@\w+", "", text)

    # Xóa ký tự đặc biệt nhưng giữ lại dấu câu cơ bản
    text = re.sub(r"[^\w\s.,?!:;'\"]", " ", text)

    # Chuyển teencode
    words = text.split()
    words = [TEENCODE_DICT.get(word, word) for word in words]
    text = " ".join(words)

    # Xóa khoảng trắng thừa
    text = re.sub(r"\s+", " ", text).strip()

    # Xóa ký tự lặp quá 2 lần (vd: "aaaaaa" -> "aa")
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)

    return text


def aggregate_comments(comments, max_comments=50):
    """
    Gộp các comment thành một đoạn text duy nhất
    Theo logic từ preprocess_new.py

    Args:
        comments: list of comment strings
        max_comments: số comment tối đa để gộp

    Returns:
        str: Các comments đã được gộp, phân cách bằng " . "
    """
    if not comments:
        return ""

    # Lọc comment rác quá ngắn (< 3 ký tự)
    filtered = [c for c in comments if c and len(str(c).strip()) > 2]

    # Giới hạn số lượng
    if len(filtered) > max_comments:
        # Random shuffle và lấy max_comments đầu tiên
        import random

        random.shuffle(filtered)
        filtered = filtered[:max_comments]

    # Gộp bằng dấu " . "
    return " . ".join(filtered)


def clean_and_aggregate_comments(raw_comments, max_comments=50):
    """
    Pipeline đầy đủ: Làm sạch từng comment rồi gộp lại

    Args:
        raw_comments: list of raw comment strings
        max_comments: số comment tối đa

    Returns:
        str: Text đã được làm sạch và gộp
    """
    if not raw_comments:
        return ""

    # Làm sạch từng comment
    cleaned = [clean_text_advanced(c) for c in raw_comments]

    # Lọc bỏ comment rỗng sau khi clean
    cleaned = [c for c in cleaned if c]

    # Gộp lại
    return aggregate_comments(cleaned, max_comments)
