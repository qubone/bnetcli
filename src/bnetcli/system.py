""""System diagnostics and dependency checks for bnetcli."""
import platform
import shutil
import subprocess
from logging import getLogger

logger = getLogger(__name__)

def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(cmd) is not None

def print_driver_hint(gpu: str):
    """Print hints for installing Vulkan drivers based on detected GPU."""
    if gpu == "Nvidia":
        logger.info("Install: nvidia-driver + vulkan-utils")
    elif gpu == "AMD":
        logger.info("Install: mesa-vulkan-drivers")
    elif gpu == "Intel":
        logger.info("Install: mesa-vulkan-drivers")

def detect_gpu() -> str:
    """Detect GPU vendor using lspci."""
    if not command_exists("lspci"):
        return "unknown"

    try:
        output = subprocess.check_output(["lspci"], text=True).lower()

        if "nvidia" in output:
            return "Nvidia"
        if "amd" in output or "radeon" in output:
            return "AMD"
        if "intel" in output:
            return "Intel"

    except Exception:
        pass

    return "unknown"


def check_vulkan() -> bool:
    """Check if Vulkan runtime is available."""
    if not command_exists("vulkaninfo"):
        return False

    try:
        subprocess.run(
            ["vulkaninfo"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False


def check_basic_dependencies() -> list[str]:
    """Check for required external tools."""
    deps = [
        "protonup",
        "vulkaninfo",
    ]

    missing = []

    for dep in deps:
        if not command_exists(dep):
            missing.append(dep)

    return missing


def print_system_summary():
    """Print system info."""
    logger.info("System diagnostics")
    logger.info("------------------")
    logger.info("OS: %s %s", platform.system(), platform.release())

    arch = platform.machine()

    if arch != "x86_64":
        logger.error("Proton requires x86_64 architecture")
        raise SystemExit(1)


    gpu: str = detect_gpu()
    logger.info("GPU detected: %s", gpu)

    if check_vulkan():
        logger.info("Vulkan: OK")
    else:
        logger.warning("Vulkan: NOT FOUND. DXVK/Proton will not work without Vulkan drivers.")
        print_driver_hint(gpu)
        raise SystemExit(1)

    missing = check_basic_dependencies()

    if missing:
        logger.info("Missing tools:")
        for m in missing:
            logger.info(" - %s", m)
        logger.info("Install missing tools using your package manager.")
        raise SystemExit(1)
    logger.info("All basic dependencies are satisfied.")
