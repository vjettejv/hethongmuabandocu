from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture
def tmp_path():
    # Keep isolated filesystem test artifacts inside the authorized workspace.
    root = Path(__file__).resolve().parents[2] / ".artifacts/phase5/unit-files"
    folder = root / uuid4().hex
    folder.mkdir(parents=True)
    return folder
