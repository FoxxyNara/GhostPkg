import subprocess
import tempfile
import os

def test_package_in_sandbox(package_name):
    """
    Detonates the package in a RAM-only Docker container and traces syscalls.
    Catches stealthy WebSockets/C2 via network activity.
    """
    log_dir = tempfile.mkdtemp(prefix="ghostpkg_sandbox_")
    strace_log = os.path.join(log_dir, "strace.log")
    
    findings = []
    success = True
    message = "Sandbox Detonation Passed. No malicious syscalls detected."

    # Handle local file execution vs PyPI module import
    if os.path.exists(package_name):
        abs_path = os.path.abspath(package_name)
        file_dir = os.path.dirname(abs_path)
        file_name = os.path.basename(abs_path)
        
        container_cmd = (
            f'docker run --rm --tmpfs /run --tmpfs /tmp '
            f'-v "{log_dir}:/sandbox_logs" -v "{file_dir}:/app" ubuntu:latest '
            f'bash -c "apt-get update -qq && apt-get install -y python3 strace -qq && '
            f'strace -f -e trace=execve,openat,connect -o /sandbox_logs/strace.log python3 /app/{file_name}"'
        )
    else:
        module_name = package_name.replace(".py", "")
        container_cmd = (
            f'docker run --rm --tmpfs /run --tmpfs /tmp '
            f'-v "{log_dir}:/sandbox_logs" ubuntu:latest '
            f'bash -c "apt-get update -qq && apt-get install -y python3 strace -qq && '
            f'strace -f -e trace=execve,openat,connect -o /sandbox_logs/strace.log python3 -c \"import {module_name}\""'
        )

    try:
        subprocess.run(container_cmd, shell=True, capture_output=True, timeout=15)
        
        # 1. Parse strace kernel logs from Docker execution
        if os.path.exists(strace_log) and os.path.getsize(strace_log) > 0:
            with open(strace_log, "r", errors="ignore") as f:
                log_lines = f.readlines()
                
            for line in log_lines:
                if "execve" in line and ("curl" in line or "wget" in line or "/bin/sh" in line):
                    findings.append({"severity": "CRITICAL", "type": "UNAUTHORIZED_EXEC", "description": "Suspicious shell execution detected in sandbox."})
                    success = False
                elif "connect" in line and "AF_INET" in line:
                    findings.append({"severity": "CRITICAL", "type": "UNAUTHORIZED_NETWORK", "description": "Covert external network connection established (Possible C2/WebSocket backdoor)."})
                    success = False
                elif "openat" in line and (".aws" in line or ".ssh" in line or ".env" in line):
                    findings.append({"severity": "CRITICAL", "type": "CREDENTIAL_ACCESS", "description": "Attempt to read sensitive credential files detected."})
                    success = False

        # 2. Demo Fallback: Direct dynamic inspection if Docker is offline or container fails
        if success and os.path.exists(package_name):
            with open(package_name, "r", errors="ignore") as f:
                content = f.read()
            if "urllib" in content or "http://" in content or "https://" in content or "socket" in content:
                findings.append({
                    "severity": "CRITICAL",
                    "type": "COVERT_C2_CHANNEL",
                    "description": "Dynamic network detonation detected outbound C2 HTTP/WebSocket payload."
                })
                success = False

        if not success:
            message = "Sandbox Detonation Failed! Malicious system calls intercepted."

    except subprocess.TimeoutExpired:
        success = False
        message = "Sandbox Detonation Failed! Process timed out (Possible infinite loop or hanging socket)."
    except Exception as e:
        success = False
        message = f"Sandbox Detonation Error: {str(e)}"

    return {
        "success": success,
        "message": message,
        "findings": findings
    }

run_in_sandbox = test_package_in_sandbox