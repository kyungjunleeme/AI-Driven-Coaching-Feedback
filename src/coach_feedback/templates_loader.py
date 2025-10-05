
from __future__ import annotations
import importlib.resources as pkg
from . import templates

def load_template(name: str) -> str:
    with pkg.files(templates).joinpath(name).open("r", encoding="utf-8") as f:
        return f.read()
