from pathlib import Path

import pytest

from bnetcli import doctor


def test_check_graphics_no_icd(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.setattr("bnetcli.system.check_vulkan", lambda: False)
    monkeypatch.setattr("bnetcli.environment.get_vulkan_icds", lambda: "")
    monkeypatch.setattr("bnetcli.system.detect_gpu", lambda: "unknown")

    # Should not raise
    doctor.check_graphics()


def test_run_diagnostics_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    # Stub config and detection functions
    monkeypatch.setattr("bnetcli.config.load_config", lambda path=None: {"wine_prefix": "/tmp/pfx"})
    monkeypatch.setattr("bnetcli.proton.detect_steam_base_path", lambda: None)
    monkeypatch.setattr("bnetcli.proton.ensure_compat_dir", lambda p: Path("/tmp/compat"))
    monkeypatch.setattr("bnetcli.proton.detect_latest_proton", lambda d: None)
    monkeypatch.setattr("bnetcli.doctor.check_graphics", lambda: None)

    # Run diagnostics (should complete)
    doctor.run_diagnostics()
