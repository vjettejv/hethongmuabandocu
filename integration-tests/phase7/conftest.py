import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))


@pytest.fixture(scope="session", autouse=True)
def explicit_runtime_opt_in():
    assert os.environ.get("PHASE7_TEST") == "1", "Run tools/verify_phase7_integration.ps1"
