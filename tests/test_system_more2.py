import platform
import subprocess

import pytest

from bnetcli import system


def test_detect_gpu_lspci_raises(monkeypatch):
    monkeypatch.setattr(system, "command_exists", lambda name: True)

    def fake_check_output(cmd, text):
        raise Exception("boom")

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    assert system.detect_gpu() == "unknown"


def test_print_system_summary_missing_tools(monkeypatch):
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(system, "detect_gpu", lambda: "Nvidia")
    monkeypatch.setattr(system, "check_vulkan", lambda: True)
    # Simulate missing tools
    monkeypatch.setattr(system, "check_basic_dependencies", lambda: ["protonup"])

    with pytest.raises(SystemExit):
        system.print_system_summary()
