import platform
import shutil
import subprocess
from typing import Any

import pytest

from bnetcli import system


def test_command_exists_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/x")
    assert system.command_exists("x")


def test_command_exists_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: None)
    assert not system.command_exists("notfound")


def test_detect_gpu_nvidia(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(system, "command_exists", lambda name: True)
    monkeypatch.setattr(subprocess, "check_output", lambda args, text: "NVIDIA Corporation ...")
    assert system.detect_gpu() == "Nvidia"


def test_detect_gpu_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(system, "command_exists", lambda name: False)
    assert system.detect_gpu() == "unknown"


def test_check_vulkan_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(system, "command_exists", lambda name: True)

    class Dummy:
        returncode = 0

    def fake_run(cmd: list[str], stdout: Any, stderr: Any, check: bool) -> Any:
        return Dummy()

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert system.check_vulkan()


def test_check_vulkan_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(system, "command_exists", lambda name: True)

    def fake_run(cmd: list[str], stdout: Any, stderr: Any, check: bool) -> None:
        raise Exception("fail")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert not system.check_vulkan()


def test_print_system_summary_arch(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force non-x86_64 to raise SystemExit
    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    with pytest.raises(SystemExit):
        system.print_system_summary()
