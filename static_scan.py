import ast
import io
import tarfile
import zipfile
import requests

EXCLUDED_PATHS = ["/test/", "/tests/", "/docs/", "/examples/"]

class SecurityASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.issues = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec", "__import__"):
                self.issues.append(f"Direct dynamic code execution via {node.func.id}()")
        elif isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr in ("system", "popen", "spawn"):
                self.issues.append(f"OS process invocation via .{attr}()")
            elif attr in ("connect", "sendto") and isinstance(node.func.value, ast.Name) and node.func.value.id == "socket":
                self.issues.append("Raw socket network transmission")
        self.generic_visit(node)

def analyze_python_source(code_str: str) -> list:
    issues = []
    try:
        tree = ast.parse(code_str)
        visitor = SecurityASTVisitor()
        visitor.visit(tree)
        issues.extend(visitor.issues)
    except SyntaxError:
        pass
    return issues

def download_and_extract_source(metadata: dict):
    urls = metadata.get("urls", [])
    if not urls:
        return None
    sdist = next((u for u in urls if u.get("packagetype") == "sdist"), urls[0])
    try:
        resp = requests.get(sdist["url"], timeout=10)
        resp.raise_for_status()
        return sdist["filename"], resp.content
    except Exception:
        return None

def run_static_scan(metadata: dict) -> dict:
    extracted = download_and_extract_source(metadata)
    if not extracted:
        return {"scanned": False, "clean": False, "findings": [], "error": "Source archive unavailable"}

    filename, raw_bytes = extracted
    findings = []

    try:
        if filename.endswith((".tar.gz", ".tgz")):
            with tarfile.open(fileobj=io.BytesIO(raw_bytes), mode="r:gz") as tar:
                for member in tar.getmembers():
                    if member.isfile() and member.name.endswith(".py"):
                        if any(p in member.name.lower() for p in EXCLUDED_PATHS):
                            continue
                        f = tar.extractfile(member)
                        if f:
                            code = f.read().decode("utf-8", errors="ignore")
                            issues = analyze_python_source(code)
                            if issues:
                                findings.append((member.name, issues))
    except Exception as e:
        return {"scanned": False, "clean": False, "findings": [], "error": str(e)}

    return {
        "scanned": True,
        "clean": len(findings) == 0,
        "findings": findings,
        "error": None
    }