# app/utils/fingerprint.py

import hashlib


def sha256_hex(data: bytes) -> str:
    """
    Return the SHA-256 hex digest of raw bytes.

    This is the canonical content fingerprint used for deduplication.
    Two files with identical bytes produce identical digests — regardless
    of filename, upload time, or uploader identity.
    """
    return hashlib.sha256(data).hexdigest()