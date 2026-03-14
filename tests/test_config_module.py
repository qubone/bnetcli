from pathlib import Path

from bnetcli import config


def test_detect_steam_path_returns_candidate(monkeypatch, tmp_path):
    # Ensure no real home interference; conftest isolates HOME
    p = config.detect_steam_path()
    # function returns a Path (per implementation summary)
    assert isinstance(p, Path)


def test_detect_proton_path_returns_candidate(monkeypatch, tmp_path):
    p = config.detect_proton_path()
    assert isinstance(p, Path)


def test_default_paths(monkeypatch):
    d = config.default_paths()
    assert "steam_path" in d and "proton_path" in d and "wine_prefix" in d
