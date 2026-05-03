import pytest
import os
import tempfile

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d
