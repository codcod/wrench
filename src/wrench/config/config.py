import tomllib
from typing import Any


def read_config(fname: str) -> dict[str, Any]:
    with open(fname, 'rb') as f:
        return tomllib.load(f)
