import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def contracts():
    return json.loads((ROOT / "contracts" / "endpoints.json").read_text(encoding="utf-8"))
