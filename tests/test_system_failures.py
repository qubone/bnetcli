import platform

import pytest

from bnetcli import system


def test_print_system_summary_vulkan_missing(monkeypatch):
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(system, "detect_gpu", lambda: "Nvidia")
    monkeypatch.setattr(system, "check_vulkan", lambda: False)
    with pytest.raises(SystemExit):
        system.print_system_summary()
