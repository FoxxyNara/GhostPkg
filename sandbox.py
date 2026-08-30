import subprocess
import tempfile
import os

def test_package_in_sandbox(package_name):
    """
    Detonates the package in a RAM-only Docker container and traces syscalls.
    Catches stealthy WebSockets/C2 via the 'connect' syscall.
    """
    # Create a temporary directory for strace logs on the host
    log_dir = tempfile.mkdtemp(prefix="ghostpkg_sandbox_")
    strace_log = os.path.join(log_dir, "strace.log")
    
    # strace command tracing execve (shells), openat (files), and connect (network/C2)
    # The container runs with a tmpfs mount so no files touch the physical disk
    container_cmd = (
        f"docker run --rm --tmpfs /run --tmpfs /tmp "
        f"-v {log_dir}:/sandbox_logs ubuntu:latest "
        f"bash -c 'apt-get update -qq && apt-get install -y python3 strace -qq && "
        f"strace -f -e trace=execve,openat,connect -o /sandbox_logs/strace.log python3 -c \"import {package_name}\"'"
    )
    
    findings = []
    success = True
    message = "Sandbox Detonation Passed. No malicious syscalls detected."
    
    try:
        # Run the sandbox detonation (Timeout after 15 seconds)
        subprocess.run(container_cmd, shell=True, capture_output=True, timeout=15)
        
        # Parse the strace log for malicious intent
        if os.path.exists(strace_log):
            with open(strace_log, "r", errors="ignore") as f:
                log_lines = f.readlines()
                
            for line in log_lines:
                # 1. Shell Execution Check
                if "execve" in line and ("curl" in line or "wget" in line or "/bin/sh" in line):
                    findings.append({"severity": "CRITICAL", "type": "UNAUTHORIZED_EXEC", "description": "Suspicious shell execution detected in sandbox."})
                    success = False
                
                # 2. Covert C2 Network Check (The WebSocket fallback at the kernel level)
                elif "connect" in line and "AF_INET" in line:
                    findings.append({"severity": "CRITICAL", "type": "UNAUTHORIZED_NETWORK", "description": "Covert external network connection established (Possible C2/WebSocket backdoor)."})
                    success = False
                    
                # 3. Credential Theft Check
                elif "openat" in line and (".aws" in line or ".ssh" in line or ".env" in line):
                    findings.append({"severity": "CRITICAL", "type": "CREDENTIAL_ACCESS", "description": "Attempt to read sensitive credential files detected."})
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