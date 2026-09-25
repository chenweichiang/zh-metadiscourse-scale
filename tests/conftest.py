"""共用設定：讓測試在未安裝套件時也能跑，並在測試期間封鎖網路連線。"""
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """任何對外連線都直接失敗，確保測試不連網 / tests must not touch the network."""
    def guard(*args, **kwargs):
        raise RuntimeError("測試不得連網 / network access is disabled in tests")

    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(socket.socket, "connect_ex", guard)
    monkeypatch.setattr(socket, "create_connection", guard)
