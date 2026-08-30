def evaluate_intent(package_name, package_category, discovered_capabilities):
    """
    Compares the declared category of the package against what its code actually does.
    """
    # Categories that have NO business opening WebSockets or C2 channels
    offline_categories = ["math", "string_manipulation", "formatting", "datetime", "utility"]
    
    findings = []
    
    # If an offline package tries to open a C2 channel, flag it immediately
    if package_category in offline_categories and "COVERT_C2_CHANNEL" in discovered_capabilities:
        findings.append({
            "severity": "CRITICAL",
            "type": "INTENT_MISMATCH",
            "description": f"A '{package_category}' package ({package_name}) should not require persistent network sockets. Malicious C2 behavior highly probable."
        })
        
    return findings