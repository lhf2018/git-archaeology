from __future__ import annotations

import hashlib


def anonymize_author(email: str, salt: str = "git-arch") -> str:
    digest = hashlib.sha256(f"{salt}:{email.lower()}".encode()).hexdigest()
    n = int(digest[:8], 16) % 9000 + 1000
    return f"Contributor#{n}"
