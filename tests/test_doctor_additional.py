import platform
import subprocess
from pathlib import Path

from bnetcli import doctor


def test__binary_exists(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/x")
    assert doctor._binary_exists("x")


def test__run_quiet_success(monkeypatch):
    class Dummy:
        def __init__(self):
            self.returncode = 0
            self.stdout = "ok"

    def fake_run(cmd, capture_output, text):
        return Dummy()

    monkeypatch.setattr(subprocess, "run", fake_run)
    code, out = doctor._run_quiet(["echo"])
    assert code == 0
    assert out == "ok"


def test__run_quiet_not_found(monkeypatch):
    def fake_run(cmd, capture_output, text):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "run", fake_run)
    code, out = doctor._run_quiet(["missing"])
    assert code == 127


def test__check_32bit_support_reports(monkeypatch):
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    # Simulate 32-bit files present
    monkeypatch.setattr(doctor.Path, "exists", lambda self: True)
    # Should not raise
    doctor._check_32bit_support()


def test__detect_mesa_version_no_glxinfo(monkeypatch):
    monkeypatch.setattr(doctor, "_binary_exists", lambda name: False)
    # Should not raise
    doctor._detect_mesa_version()


def test__detect_session_type(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    doctor._detect_session_type()


def test__check_flatpak_steam(monkeypatch):
    # Provide a path containing flatpak identifier
    doctor._check_flatpak_steam(Path("/var/lib/flatpak/app/com.valvesoftware.Steam"))
