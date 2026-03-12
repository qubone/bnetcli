from pathlib import Path

import pytest

from bnetcli import doctor


def test__check_32bit_support_not_x86(
    capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("platform.machine", lambda: "arm64")
    doctor._check_32bit_support()
    out = capsys.readouterr().out
    assert "System is not x86_64" in out


def test__detect_session_type_x11_and_unknown(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    doctor._detect_session_type()
    out = capsys.readouterr().out
    assert "Running under X11 session" in out

    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    doctor._detect_session_type()
    out = capsys.readouterr().out
    assert "Session type unknown" in out


def test__check_flatpak_steam_detected(capsys: pytest.CaptureFixture) -> None:
    # Path containing flatpak identifier should trigger warning
    p = Path("/var/lib/flatpak/app/com.valvesoftware.Steam/data")
    doctor._check_flatpak_steam(p)
    out = capsys.readouterr().out
    assert "Steam Flatpak detected" in out


def test_check_graphics_gpu_variants(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    # NVIDIA branch
    monkeypatch.setattr("bnetcli.doctor.detect_gpu", lambda: "NVIDIA")
    monkeypatch.setattr("bnetcli.doctor.check_vulkan", lambda: True)
    monkeypatch.setattr("bnetcli.doctor.get_vulkan_icds", lambda: "icd")
    doctor.check_graphics()
    out = capsys.readouterr().out
    assert "Detected NVIDIA GPU" in out

    # AMD branch
    monkeypatch.setattr("bnetcli.doctor.detect_gpu", lambda: "AMD")
    doctor.check_graphics()
    out = capsys.readouterr().out
    assert "Detected AMD GPU" in out


def test_run_diagnostics_no_steam_no_proton(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    tmp_path: Path,
) -> None:
    # Simulate no steam, no proton installed and no protonup
    monkeypatch.setattr(
        "bnetcli.config.load_config", lambda p=None: {"wine_prefix": str(tmp_path / "p")}
    )
    monkeypatch.setattr("bnetcli.proton.detect_steam_base_path", lambda: None)
    monkeypatch.setattr("bnetcli.proton.ensure_compat_dir", lambda p: tmp_path / "compat")
    monkeypatch.setattr("bnetcli.doctor._binary_exists", lambda name: False)
    monkeypatch.setattr("bnetcli.proton.detect_latest_proton", lambda d: None)
    monkeypatch.setattr("bnetcli.doctor.check_graphics", lambda: None)

    doctor.run_diagnostics()
    out = capsys.readouterr().out
    assert "Steam not detected (fallback mode active)" in out
    assert "No GE-Proton version detected" in out
