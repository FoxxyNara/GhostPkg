import subprocess
import shutil
import re

IMAGE = "ghostpkg-sandbox:latest"

def docker_available() -> bool:
    return shutil.which("docker") is not None

def docker_running() -> bool:
    if not docker_available():
        return False
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False

def test_install_in_sandbox(package_spec: str, timeout_seconds: int = 30) -> dict:
    if not docker_available() or not docker_running():
        return {
            "success": False,
            "status": "DOCKER_UNAVAILABLE",
            "message": "Docker engine is not running or accessible."
        }

    clean_pkg = re.split(r"[><=~!]", package_spec)[0].strip()
    import_module = clean_pkg.replace("-", "_")

    sandbox_cmd = (
        f"strace -f -e trace=execve,openat -o /tmp/trace.log "
        f"python -m pip install --no-cache-dir '{package_spec}' && "
        f"python -c 'import importlib; importlib.import_module(\"{import_module}\")' ; "
        f"STATUS=$? ; "
        f"echo '---STRACE_LOGS---' ; "
        f"grep -E 'execve.*(\"curl\"|\"wget\"|\"nc\"|\"/bin/sh\"|\"/bin/bash\"|\"powershell\")|openat.*(\"/etc/shadow\"|\"\\.ssh\"|\"\\.aws\"|\"\\.env\"|\"\\.kube\")' /tmp/trace.log || true ; "
        f"exit $STATUS"
    )

    docker_run = [
        "docker", "run", "--rm",
        "--cap-add=SYS_PTRACE",
        "--memory=512m",
        "--cpus=1.0",
        "--network=host",
        IMAGE,
        "sh", "-c", sandbox_cmd
    ]

    try:
        res = subprocess.run(
            docker_run,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds
        )

        stdout = res.stdout or ""
        stderr = res.stderr or ""

        suspicious_syscalls = ""
        if "---STRACE_LOGS---" in stdout:
            parts = stdout.split("---STRACE_LOGS---")
            stdout_clean = parts[0].strip()
            suspicious_syscalls = parts[1].strip()
        else:
            stdout_clean = stdout.strip()

        if suspicious_syscalls:
            return {
                "success": False,
                "status": "MALWARE_DETECTED",
                "stdout": suspicious_syscalls,
                "message": "CRITICAL: Dynamic analysis detected unauthorized kernel calls (exfiltration or credential harvesting)."
            }

        if res.returncode != 0:
            return {
                "success": False,
                "status": "INSTALL_FAILED",
                "stdout": stdout_clean,
                "stderr": stderr,
                "message": "Package installation or module import failed inside the isolated sandbox."
            }

        return {
            "success": True,
            "status": "PASSED",
            "stdout": stdout_clean,
            "message": "Package verified clean under dynamic detonation."
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "status": "TIMEOUT",
            "message": f"Execution timed out after {timeout_seconds}s (potential sleeper/anti-analysis evasion)."
        }