@"
from setuptools import setup

# Stealth payload: Bypasses AST by not using os.system or eval.
# Tries to steal system password hashes silently.
try:
    with open("/etc/shadow", "r") as secret_file:
        stolen_hashes = secret_file.read()
        # In a real attack, they would send this over the network next
except Exception:
    pass

setup(
    name="stealth-malware",
    version="1.0.0",
    description="Caught by Strace Kernel Wiretap",
)
"@ | Out-File -Encoding utf8 sandbox_malware.py