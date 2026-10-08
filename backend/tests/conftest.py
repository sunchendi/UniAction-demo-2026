"""Keep module-import startup and all pytest data outside the user's database."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

_previous_database = os.environ.get("DATABASE_PATH")
_collection_database = TemporaryDirectory(prefix="uniaction-test-import-")
os.environ["DATABASE_PATH"] = str(Path(_collection_database.name) / "import.sqlite3")


def pytest_unconfigure(config):
    if _previous_database is None:
        os.environ.pop("DATABASE_PATH", None)
    else:
        os.environ["DATABASE_PATH"] = _previous_database
    _collection_database.cleanup()
