import argparse
import json
import os
import subprocess
import sys

# Force the Python path to recognize the current directory first
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import static_scan

try:
    from pypi_check import run_security_check  # type: ignore[import-not-found]
except ImportError:
    def run_security_check(*args, **kwargs):
        raise ModuleNotFoundError(
            "pypi_check is not available. Ensure it is installed or placed beside cli.py."
        )

def install_on_host(package_name, silent=False):
    """Executes native pip install on the host machine."""
    if not silent:
        print(f"\n[GhostPkg] Verification complete. Routing '{package_name}' to native system pip...")

    try:
        kwargs = {}
        if silent:
            kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.PIPE}

        subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            check=True,
            **kwargs
        )
        if not silent:
            print(f"\n✅ SUCCESS: '{package_name}' is safely installed on your system.")
        return True
    except subprocess.CalledProcessError:
        if not silent:
            print(f"\n❌ ERROR: System pip failed to install '{package_name}'.")
        return False

def show_result(package_name, result):
    verdict = result.get("verdict", {})
    print(f"\n📦 Package: {package_name}")

    if verdict.get("exists") is True:
        print("PyPI: EXISTS (or Bypassed for Local File)")
    elif verdict.get("exists") is False:
        print("PyPI: NOT FOUND (Hallucination Detected)")
    else:
        print("PyPI: UNKNOWN")

    if verdict.get("closest_match"):
        print(f"💡 Suggestion: Did you mean '{verdict['closest_match']}'?")

    scan = result.get("scan")
    if scan and scan.get("findings"):
        print("\n🚨 CRITICAL AST VIOLATIONS DETECTED:")
        for path, patterns in scan["findings"]:
            for issue in patterns:
                print(f"  ❌ [{path}] -> {issue}")

    sandbox = result.get("sandbox")
    if sandbox:
        print(f"\n🧪 Docker sandbox status: {sandbox.get('status')}")
        if sandbox.get("status") == "MALWARE_DETECTED" and sandbox.get("stdout"):
            print(f"🚨 Intercepted Syscalls:\n{sandbox['stdout']}")

    print(f"\nStage: {result.get('stage')}")
    print(f"Message: {result.get('message')}")

    if result.get("success"):
        print("\n🛡️ STATUS: APPROVED (Checks Passed)")
        if not install_on_host(package_name, silent=False):
            sys.exit(1)
    else:
        print("\n🛑 STATUS: BLOCKED (Installation Halted)")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(prog="ghostpkg", description="Zero-Trust AI Dependency Firewall")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Check and safely install a package")
    install_parser.add_argument("package", help="Package name to install")
    install_parser.add_argument("--json", action="store_true", help="Output strict JSON for Agent integration")
    install_parser.add_argument("--local", action="store_true", help="Bypass PyPI triage and scan a local file directly")

    args = parser.parse_args()

    if args.command == "install":
        if args.local:
            print(f"\n[GhostPkg] 🔍 LOCAL MODE: Bypassing PyPI triage for '{args.package}'...")
            
            try:
                # utf-8-sig ensures hidden PowerShell BOM characters are stripped
                with open(args.package, "r", encoding="utf-8-sig") as f:
                    code_content = f.read()
            except FileNotFoundError:
                print(f"\n❌ ERROR: Could not find local file '{args.package}'")
                sys.exit(1)
                
            issues = static_scan.analyze_python_source(code_content)
            
            if issues:
                result = {
                    "success": False,
                    "stage": "static_scan",
                    "message": "Execution Blocked by Tier 2 Defense!",
                    "verdict": {"exists": True},
                    "scan": {"findings": [(args.package, issues)]},
                    "sandbox": None
                }
            else:
                print("[GhostPkg] Tier 2 Static AST scan passed. Escalating to Tier 3 Docker Sandbox...")
                import sandbox
                sandbox_result = sandbox.test_local_script_in_sandbox(args.package)
                
                result = {
                    "success": sandbox_result.get("success", False),
                    "stage": "sandbox",
                    "message": sandbox_result.get("message"),
                    "verdict": {"exists": True},
                    "scan": {"findings": []},
                    "sandbox": sandbox_result
                }
        else:
            result = run_security_check(args.package)

        if args.json:
            if not result.get("success") and result.get("verdict", {}).get("closest_match"):
                result["action_required"] = "RETRY_WITH_SUGGESTION"
                result["remediation_command"] = f"ghostpkg install {result['verdict']['closest_match']}"
            else:
                result["action_required"] = "NONE"
            print(json.dumps(result))
            sys.exit(0 if result.get("success") else 1)

        show_result(args.package, result)

if __name__ == "__main__":
    main()
