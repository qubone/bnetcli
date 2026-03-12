from pathlib import Path

from bnetcli import proton


def test_install_calls_protonup(monkeypatch):
    calls = []

    # Patch symbols imported into proton module
    monkeypatch.setattr(proton, "require_binary", lambda name: None)

    def fake_run(cmd):
        calls.append(cmd)

    monkeypatch.setattr(proton, "run", fake_run)

    proton.install("vtest", Path("/tmp/compat"))
    assert calls
    assert "protonup" in calls[0][0]


def test_remove_calls_protonup(monkeypatch):
    calls = []
    monkeypatch.setattr(proton, "require_binary", lambda name: None)

    def fake_run(cmd):
        calls.append(cmd)

    monkeypatch.setattr(proton, "run", fake_run)
    proton.remove("GE-ProtonX")
    assert calls
    assert calls[0][0] == "protonup"


def test_detect_steam_base_path_with_candidates(tmp_path, monkeypatch):
    # Monkeypatch Path.home to tmp_path so candidates are under tmp_path
    monkeypatch.setattr(proton.Path, "home", lambda: tmp_path)

    # Create a candidate Steam path
    p = tmp_path / ".local" / "share" / "Steam"
    p.mkdir(parents=True)

    detected = proton.detect_steam_base_path()
    assert detected == p


def test_ensure_compat_dir_uses_configured(tmp_path):
    cfg = tmp_path / "custom_compat"
    res = proton.ensure_compat_dir(cfg)
    assert res.exists()
