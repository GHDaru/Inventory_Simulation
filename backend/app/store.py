"""
In-memory storage for datasets and simulation runs.
"""
from threading import Lock

datasets: dict = {}   # id -> dataset dict
runs: dict = {}       # id -> run dict
_lock = Lock()
