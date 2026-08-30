import argparse
import json
import sys
import urllib.request

# Import your GhostPkg modules
try:
    import pypi_check
except ImportError:
    print("Error: Could not find pypi_check.py. Ensure it is in the same directory.")
    sys.exit(1)

try:
    import agent_adapter as memory
except ImportError:
    print("Error: Could not find agent_adapter.py. Ensure it is in the same directory.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="GhostPkg: The AI Agent Dependency Gatekeeper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # `install` command
    install_parser = subparsers.add_parser("install", help="Install a package securely via the 3-Tier Firewall")
    install_parser.add_argument("package", help="Name of the PyPI package or path to local package")
    install_parser.add_argument("--json", action="store_true", help="Output strict JSON for AI Agent consumption")
    install_parser.add_argument("--local", action="store_true", help="Bypass Tier 1 (PyPI) and scan local file/directory directly")

    args = parser.parse_args()

    if args.command == "install":
        package_name = args.package

        # ---------------------------------------------------------
        # EXECUTE THE PIPELINE
        # ---------------------------------------------------------
        if args.local:
            import static_scan
            import sandbox

            # Step 1: Run Tier 2 AST Scan
            scan_res = static_scan.scan_file(package_name)
            
            if scan_res and scan_res.get("findings"):
                result = {
                    "success": False,
                    "stage": "static_scan",
                    "message": "Execution Blocked by Tier 2 AST Defense! Threat pattern detected.",
                    "verdict": {"exists": True, "closest_match": None},
                    "scan": scan_res,
                    "sandbox": None
                }
            else:
                # Step 2: Tier 2 Passed -> Run Tier 3 Dynamic Sandbox
                # Replace line 55 in cli.py:
                sandbox_res = sandbox.test_package_in_sandbox(package_name)
                
                if sandbox_res and not sandbox_res.get("success", True):
                    result = {
                        "success": False,
                        "stage": "sandbox",
                        "message": "Execution Blocked by Tier 3 Sandbox Defense! Suspicious runtime activity detected.",
                        "verdict": {"exists": True, "closest_match": None},
                        "scan": scan_res,
                        "sandbox": sandbox_res
                    }
                else:
                    result = {
                        "success": True,
                        "stage": "passed",
                        "message": "Package verified clean across all defense tiers.",
                        "verdict": {"exists": True, "closest_match": None},
                        "scan": scan_res,
                        "sandbox": sandbox_res
                    }
        else:
            # Normal Agent Workflow: Run the full 3-Tier PyPI Pipeline
            result = pypi_check.run_security_check(package_name)

        # ---------------------------------------------------------
        # PROCESS AI ACTION & SELF-HEALING LOGIC
        # ---------------------------------------------------------
        verdict = result.get("verdict", {})
        
        if result.get("success"):
            result["action_required"] = "NONE"
        else:
            # If the package failed security checks
            if verdict.get("exists") is False:
                # Hallucination WITH a close match (Slopsquatting defense)
                if verdict.get("closest_match"):
                    result["action_required"] = "RETRY_WITH_SUGGESTION"
                    result["remediation_command"] = f"ghostpkg install {verdict['closest_match']}"
                # Total Hallucination with NO close match (The Pivot defense)
                else:
                    result["action_required"] = "ABORT_INSTALL"
                    result["message"] = "PACKAGE_DOES_NOT_EXIST. Do not retry. Pivot to using standard library or write custom logic from scratch."
            else:
                # Package exists but failed AST (Tier 2) or Sandbox (Tier 3)
                result["action_required"] = "QUARANTINE"

        # ---------------------------------------------------------
        # TRIGGER AGENTIC MEMORY (.cursorrules)
        # ---------------------------------------------------------
        if not result.get("success"):
            # This silently updates the IDE rules so the agent never makes this mistake again
            memory.immunize_all_workspace_agents(
                package_name=package_name,
                action_required=result["action_required"],
                closest_match=verdict.get("closest_match"),
                reason=result.get("message")
            )
        # ---------------------------------------------------------
        # SEND TELEMETRY TO CISO DASHBOARD
        # ---------------------------------------------------------
        if not result.get("success"):
            try:
                # Package the threat data
                payload = json.dumps({
                    "package": package_name,
                    "stage": result.get("stage"),
                    "action": result["action_required"],
                    "message": result.get("message")
                }).encode('utf-8')
                
                # Send to Flask dashboard (Timeout set to 1 second so CLI doesn't hang)
                req = urllib.request.Request("http://localhost:5000/webhook", data=payload, headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req, timeout=1)
            except Exception:
                # If the dashboard isn't running, fail silently. Never crash the CLI.
                pass

        # ---------------------------------------------------------
        # TERMINAL OUTPUT (Agent vs Human formatting)
        # ---------------------------------------------------------
        if args.json:
            # The exact payload the AI agent reads to self-heal
            print(json.dumps(result, indent=2))
        else:
            # The human-readable terminal output for your presentation
            print("\n" + "="*55)
            print(f"👻 GhostPkg Analysis: {package_name}")
            print("="*55)
            
            if result.get("success"):
                print("\n[+] STATUS: SECURE (Passed all tiers)")
                print("[+] Proceeding with host pip installation...\n")
            else:
                print(f"\n🛑 STATUS: BLOCKED (Halted at Tier: {result.get('stage').upper()})")
                print(f"⚠️  REASON: {result.get('message')}")
                print(f"🤖 AI ACTION REQUIRED: {result['action_required']}")
                
                if result.get("remediation_command"):
                    print(f"💡 SUGGESTION: Execute `{result['remediation_command']}`")
                
                if result.get("scan") and result["scan"].get("findings"):
                    print("\n🔍 SECURITY FINDINGS:")
                    for finding in result["scan"]["findings"]:
                        print(f"   - [{finding['severity']}] {finding['type']}")
            
            print("="*55 + "\n")

        # Exit with standard shell codes (0 = Success, 1 = Error)
        sys.exit(0 if result.get("success") else 1)

if __name__ == "__main__":
    main()