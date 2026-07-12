import importlib
import os
import sqlite3
import sys
import uuid
from pathlib import Path
from unittest import mock

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "tests" / ".runtime"
RUNTIME_DIR.mkdir(exist_ok=True)


def _load_backend_module():
    sys.path.insert(0, str(ROOT))
    runtime_db = RUNTIME_DIR / "import_runtime.db"
    os.environ["DFINANS_RUNTIME_DB_PATH"] = str(runtime_db)
    with mock.patch("threading.Thread.start", return_value=None):
        return importlib.import_module("dfinans_live_backend")


@pytest.fixture(scope="session")
def backend_module():
    return _load_backend_module()


@pytest.fixture()
def isolated_runtime_db(backend_module, monkeypatch):
    db_path = RUNTIME_DIR / f"runtime_{uuid.uuid4().hex}.sqlite3"
    monkeypatch.setattr(backend_module, "RUNTIME_DB_PATH", str(db_path))
    backend_module.init_runtime_db()
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture()
def runtime_db_connection(isolated_runtime_db):
    conn = sqlite3.connect(isolated_runtime_db)
    try:
        yield conn
    finally:
        conn.close()
