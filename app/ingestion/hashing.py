from __future__ import annotations

import hashlib
from pathlib import Path

"""
Checksums identify the original source bytes, not normalized text.

Files that normalize to identical text remain distinct source artifacts when
their original bytes differ.
"""

def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    with path.open("rb") as file_handle:
        digest = hashlib.file_digest(
            file_handle,
            "sha256",
        )

    return digest.hexdigest()