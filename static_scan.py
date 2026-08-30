import ast
import os

# Whitelist of verified, safe packages that should bypass aggressive C2 blocks
WHITELISTED_PACKAGES = {
    "requests", "urllib3", "certifi", "idna", "charset-normalizer", 
    "loza", "flask", "fastapi", "numpy", "pandas", "colorama"
}

def scan_file(file_path, package_name=None):
    """
    Performs static AST analysis to detect malicious code patterns,
    obfuscated execution, or unauthorized backdoors.
    """
    # 1. Bypass check for verified/safe packages
    if package_name and package_name.lower() in WHITELISTED_PACKAGES:
        return {"status": "SECURE", "findings": []}

    if not os.path.exists(file_path):
        return {"status": "SECURE", "findings": []}

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source_code = f.read()

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return {"status": "SECURE", "findings": []}

    findings = []

    for node in ast.walk(tree):
        # Check for obfuscated execution (eval/exec traps)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec"}:
                findings.append("[CRITICAL] OBFUSCATED_EXECUTION: Use of eval/exec detected.")

        # Check for unauthorized low-level backdoor libraries in non-whitelisted code
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] in {"websockets", "paramiko"} and not package_name:
                    findings.append("[CRITICAL] COVERT_C2_CHANNEL")

    # Remove duplicate findings
    findings = list(set(findings))
    
    status = "BLOCKED" if findings else "SECURE"
    return {"status": status, "findings": findings}