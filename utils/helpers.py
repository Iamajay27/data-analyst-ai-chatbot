from __future__ import annotations
import re

def human_bytes(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"

def normalize_name(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._ -]+", "", str(name))
    return name.strip()[:100]
