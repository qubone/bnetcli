import platform
import subprocess

import pytest

from bnetcli import system


def test_check_basic_dependencies_reports(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate protonup missing, vulkaninfo missing
    monkeypatch.setattr(system, "command_exists", lambda name: False)
    missing = system.check_basic_dependencies()
    assert "protonup" in missing


def test_print_driver_hint_logs(caplog: pytest.LogCaptureFixture) -> None:
    import logging
    caplog.clear()
    caplog.set_level(logging.INFO)
    system.print_driver_hint("Nvidia")
    system.print_driver_hint("AMD")
    system.print_driver_hint("Intel")
    assert any("nvidia-driver" in rec.getMessage() for rec in caplog.records)
    assert any("mesa-vulkan-drivers" in rec.getMessage() for rec in caplog.records)


def test_print_system_summary_success(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    # Simulate a healthy system
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(system, "detect_gpu", lambda: "Nvidia")
    monkeypatch.setattr(system, "check_vulkan", lambda: True)
    monkeypatch.setattr(system, "check_basic_dependencies", lambda: [])
    import logging
    caplog.set_level(logging.INFO)
    # Should not raise
    system.print_system_summary()
    assert any("All basic dependencies are satisfied" in r.getMessage() for r in caplog.records)


def test_detect_gpu_amd_intel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(system, "command_exists", lambda name: True)
    monkeypatch.setattr(subprocess, "check_output", lambda args, text: "AMD Radeon")
    assert system.detect_gpu() == "AMD"
    monkeypatch.setattr(subprocess, "check_output", lambda args, text: "Intel Corporation")
    assert system.detect_gpu() == "Intel"
