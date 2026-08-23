from __future__ import annotations

import sys
from pathlib import Path
import shutil
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))


@pytest.fixture
def local_tmp_path() -> Path:
    root = Path(__file__).parents[1] / ".test-artifacts"
    path = root / uuid4().hex
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
