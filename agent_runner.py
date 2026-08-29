# File: agent_runner.py
import subprocess
import json
import time

def simulate_ai_thought(thought):
    """Fakes the delay and terminal output of an AI agent thinking."""
    print(f"\n🤖 [AI Agent Worker]: {thought}")
    time.sleep(1.5)

def run_agent_workflow():
    print("=" * 70)
    print(" 🚀 INITIATING AUTONOMOUS DEV-AGENT WORKFLOW")
    print("=" * 70)
    
    simulate_ai_thought("I need to fetch data from an API.")
    simulate_ai_thought("I will install the 'reqeusts' library to handle HTTP calls.")
    
    # 1. The Agent makes a common typo/hallucination
    target_package = "reqeusts"
    install_command = ["python", "cli.py", "install", target_package, "--json"]
    
    simulate_ai_thought(f"Executing system command: {' '.join(install_command)}")
    
    # 2. Agent runs GhostPkg in --json mode
    result = subprocess.run(install_command, capture_output=True, text=True)
    
    # 3. Agent parses the GhostPkg JSON telemetry
    try:
        security_payload = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        print("🚨 Agent crashed: Standard pip error or non-JSON output received.")
        print(f"Raw output: {result.stdout}")
        return

    # 4. The Self-Healing Logic Loop
    if not security_payload["success"]:
        simulate_ai_thought(f"GhostPkg Firewall BLOCKED my command. Reason: {security_payload['message']}")
        
        # Check the deterministic contract GhostPkg gave us
        action = security_payload.get("action_required")
        
        if action == "RETRY_WITH_SUGGESTION":
            remediation = security_payload.get("remediation_command")
            suggested = security_payload["verdict"]["closest_match"]
            
            simulate_ai_thought(f"Reading GhostPkg telemetry...")
            simulate_ai_thought(f"Ah, I made a typo. The correct package is '{suggested}'.")
            simulate_ai_thought(f"Self-Correcting. Executing remediation: {remediation} --json")
            
            # 5. Agent autonomously executes the suggested remediation
            
            # --- PATCH FOR LOCAL TESTING ---
            # Translate the global 'ghostpkg' command into our local python script
            remediation = remediation.replace("ghostpkg", "python cli.py")
            # -------------------------------
            
            retry_command = remediation.split() + ["--json"]
            retry_result = subprocess.run(retry_command, capture_output=True, text=True)
            
            try:
                retry_payload = json.loads(retry_result.stdout.strip())
                
                if retry_payload["success"]:
                    simulate_ai_thought(f"✅ Self-Healing successful. '{suggested}' installed safely. Resuming coding tasks...")
                else:
                    simulate_ai_thought("❌ Remediation failed. Halting workflow and requesting human intervention.")
            except json.JSONDecodeError:
                simulate_ai_thought(f"❌ Remediation failed. Invalid response from GhostPkg.\nRaw: {retry_result.stdout}")