import os
from datetime import datetime

TARGET_IDE_RULES = {
    ".cursorrules": "Cursor IDE",
    ".windsurfrules": "Windsurf IDE",
    "CLAUDE.md": "Claude Code CLI",
    "AGENT.md": "Generic Dev Agent"
}

def build_immunization_rule(package_name, action_required, closest_match=None, reason=None) -> str:
    """Formats a deterministic system instruction for AI context parsers."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    rule = f"\n# [GhostPkg Auto-Immunization | {timestamp}]\n"
    rule += f"CRITICAL SECURITY RULE: You previously attempted to install package '{package_name}'. "
    rule += "This operation was intercepted and BLOCKED by the GhostPkg Firewall.\n"

    if action_required == "RETRY_WITH_SUGGESTION" and closest_match:
        rule += f"CORRECTION: '{package_name}' is a hallucinated slopsquat typo. Use '{closest_match}' instead for all future operations.\n"
    elif action_required == "ABORT_INSTALL":
        rule += "CORRECTION: This package does not exist on PyPI. DO NOT retry. Pivot to using Python standard libraries (e.g., urllib, json) or write custom code.\n"
    elif action_required == "QUARANTINE":
        rule += f"CORRECTION: Package '{package_name}' exhibited malicious behavior (Reason: {reason or 'Unauthorized syscalls / C2 socket'}). Never attempt to install or import this dependency.\n"
    else:
        rule += f"CORRECTION: Do not attempt to install or suggest '{package_name}'.\n"

    return rule

def immunize_all_workspace_agents(package_name, action_required, closest_match=None, reason=None, create_if_missing=False):
    """
    Scans the current working directory for AI IDE configuration files 
    and writes/appends the security immunization rule across all detected tools.
    """
    rule_entry = build_immunization_rule(package_name, action_required, closest_match, reason)
    updated_files = []

    for rule_file, ide_name in TARGET_IDE_RULES.items():
        # Check if the file exists or if we should explicitly initialize .cursorrules
        if os.path.exists(rule_file) or (create_if_missing and rule_file == ".cursorrules"):
            try:
                with open(rule_file, "a", encoding="utf-8") as f:
                    f.write(rule_entry)
                updated_files.append(f"{rule_file} ({ide_name})")
            except Exception as e:
                print(f"[-] Failed to update {rule_file}: {e}")

    if updated_files:
        print(f"\n[+] Multi-IDE Immunization Sync Complete:")
        for file_info in updated_files:
            print(f"    ✔ Synchronized rule to {file_info}")
        return True
    else:
        # Fallback: Default to creating .cursorrules if no files exist yet
        try:
            with open(".cursorrules", "a", encoding="utf-8") as f:
                f.write(rule_entry)
            print(f"\n[+] Immunized workspace via default .cursorrules file.")
            return True
        except Exception as e:
            print(f"[-] Workspace immunization failed: {e}")
            return False

if __name__ == "__main__":
    # Test execution for verification
    immunize_all_workspace_agents(
        package_name="reqeusts",
        action_required="RETRY_WITH_SUGGESTION",
        closest_match="requests"
    )