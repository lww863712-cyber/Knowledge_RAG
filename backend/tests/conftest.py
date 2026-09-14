import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Path:
    with tempfile.TemporaryDirectory(dir=".") as directory:
        yield Path(directory)