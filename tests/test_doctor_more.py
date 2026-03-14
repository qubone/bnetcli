from pathlib import Path

import pytest

from bnetcli import doctor


def test_check_graphics_vulkan_fail(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    # Vulkan present but check_vulkan reports False
    monkeypatch.setattr("bnetcli.system.check_vulkan", lambda: False)
    monkeypatch.setattr("bnetcli.environment.get_vulkan_icds", lambda: "")
    monkeypatch.setattr("bnetcli.system.detect_gpu", lambda: "unknown")

    # Should not raise; prints warnings
    doctor.check_graphics()
    out = capsys.readouterr().out
    assert "[Vulkan]" in out


def test_detect_mesa_version_with_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.setattr(doctor, "_binary_exists", lambda name: True)
    monkeypatch.setattr(doctor, "_run_quiet", lambda cmd: (0, "some line\nOpenGL version string: 3.0\nother"))
    doctor._detect_mesa_version()
    out = capsys.readouterr().out
    assert "OpenGL version string" in out


def test_run_diagnostics_with_steam_and_proton(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    # Provide a config and simulate steam/proton present to hit branches
    monkeypatch.setattr("bnetcli.config.load_config", lambda p=None: {"wine_prefix": "/tmp/p"})
    monkeypatch.setattr(doctor, "detect_steam_base_path", lambda: Path("/tmp/steam"))
    monkeypatch.setattr(doctor, "ensure_compat_dir", lambda p: Path("/tmp/compat"))
    monkeypatch.setattr(doctor, "_binary_exists", lambda name: True)
    monkeypatch.setattr(doctor, "detect_latest_proton", lambda d: "GE-ProtonX")
    monkeypatch.setattr(doctor, "check_graphics", lambda: None)

    doctor.run_diagnostics()
    out = capsys.readouterr().out
    assert "=== Diagnostics Complete ===" in out
