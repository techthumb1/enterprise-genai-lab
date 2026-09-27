from app.ingestion.hashing import sha256_bytes


def test_sha256_bytes_is_deterministic() -> None:
    digest = sha256_bytes(b"hello")

    assert digest == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29"
        "e1b161e5c1fa7425e73043362938b9824"
    )