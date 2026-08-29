import difflib
import requests

try:
    from static_scan import run_static_scan  # type: ignore
except ImportError:
    def run_static_scan(metadata):
        return {"scanned": False, "clean": False, "findings": [], "error": "static_scan module not found"}

try:
    from sandbox import test_install_in_sandbox  # type: ignore
except ImportError:
    def test_install_in_sandbox(package_name):
        return {"success": False, "status": "SANDBOX_MISSING", "error": "sandbox module not found", "stdout": "", "stderr": ""}

TOP_100_PACKAGES = [
    "requests", "urllib3", "boto3", "botocore", "setuptools", "pip", "wheel",
    "numpy", "pandas", "scipy", "matplotlib", "scikit-learn", "seaborn",
    "django", "flask", "fastapi", "starlette", "uvicorn", "gunicorn",
    "sqlalchemy", "pydantic", "jinja2", "werkzeug", "click", "typer",
    "pytest", "tox", "nose", "coverage", "mock",
    "pyyaml", "toml", "python-dotenv", "attrs", "packaging",
    "certifi", "charset-normalizer", "idna", "six", "python-dateutil",
    "pytz", "tzdata",
    "cryptography", "pyjwt", "bcrypt",
    "pillow", "opencv-python", "imageio", "scikit-image",
    "beautifulsoup4", "lxml", "html5lib", "soupsieve",
    "selenium", "playwright", "scrapy",
    "tensorflow", "torch", "torchvision", "keras", "transformers",
    "huggingface-hub", "tokenizers", "sentencepiece",
    "openai", "anthropic", "langchain", "langchain-core",
    "boto", "azure-storage-blob", "google-cloud-storage",
    "redis", "pymongo", "psycopg2", "mysqlclient",
    "celery", "kombu", "billiard",
    "gevent", "eventlet", "greenlet",
    "tqdm", "rich", "colorama", "tabulate",
    "loguru", "structlog",
    "pyparsing", "regex", "markupsafe",
    "protobuf", "grpcio", "googleapis-common-protos",
    "aiohttp", "httpx", "websockets",
    "flake8", "black", "isort", "mypy", "pylint",
    "sphinx", "mkdocs",
]


def normalize_name(package_name):
    return package_name.strip().lower().replace("_", "-")


def find_closest_match(package_name, cutoff=0.75):
    normalized_input = normalize_name(package_name)
    normalized_packages = [normalize_name(p) for p in TOP_100_PACKAGES]
    matches = difflib.get_close_matches(normalized_input, normalized_packages, n=1, cutoff=cutoff)
    if not matches:
        return None
    closest = matches[0]
    if closest == normalized_input:
        return None
    return closest


def fetch_pypi_metadata(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return {"status": "found", "metadata": response.json()}
        if response.status_code == 404:
            return {"status": "not_found", "metadata": None}
        return {"status": "error", "metadata": None}
    except requests.RequestException:
        return {"status": "error", "metadata": None}


def check_package(package_name):
    normalized = normalize_name(package_name)

    if not normalized:
        return {
            "package": package_name, "exists": False, "status": "blocked",
            "reason": "empty_package_name", "closest_match": None, "metadata": None,
        }

    result = fetch_pypi_metadata(normalized)

    if result["status"] == "error":
        return {
            "package": package_name, "exists": None, "status": "unknown",
            "reason": "pypi_lookup_failed",
            "closest_match": find_closest_match(package_name), "metadata": None,
        }

    if result["status"] == "not_found":
        return {
            "package": package_name, "exists": False, "status": "blocked",
            "reason": "package_not_found",
            "closest_match": find_closest_match(package_name), "metadata": None,
        }

    return {
        "package": package_name, "exists": True, "status": "exists",
        "reason": "package_exists",
        "closest_match": find_closest_match(package_name),
        "metadata": result["metadata"],
    }


def run_security_check(package_name):
    verdict = check_package(package_name)

    if verdict["status"] == "unknown":
        return {
            "success": False, "stage": "pypi", "package": package_name,
            "verdict": verdict, "scan": None, "sandbox": None,
            "message": "Unable to verify package existence because PyPI lookup failed.",
        }

    if verdict["exists"] is False:
        return {
            "success": False, "stage": "pypi", "package": package_name,
            "verdict": verdict, "scan": None, "sandbox": None,
            "message": "Package does not exist on PyPI.",
        }

    normalized = normalize_name(package_name)
    trusted_list = [normalize_name(p) for p in TOP_100_PACKAGES]
    is_trusted = normalized in trusted_list

    scan_result = None
    if not is_trusted:
        scan_result = run_static_scan(verdict["metadata"])

        if not scan_result.get("scanned", False):
            return {
                "success": False, "stage": "static_scan", "package": package_name,
                "verdict": verdict, "scan": scan_result, "sandbox": None,
                "message": f"Could not verify package source ({scan_result.get('error')}); blocking to be safe.",
            }

        if not scan_result.get("clean", False):
            return {
                "success": False, "stage": "static_scan", "package": package_name,
                "verdict": verdict, "scan": scan_result, "sandbox": None,
                "message": "Dangerous code patterns found in package source.",
            }

    sandbox_result = test_install_in_sandbox(package_name)

    if not sandbox_result.get("success", False):
        return {
            "success": False, "stage": "sandbox", "package": package_name,
            "verdict": verdict, "scan": scan_result, "sandbox": sandbox_result,
            "message": sandbox_result.get("message", "Package failed Docker sandbox testing."),
        }

    return {
        "success": True, "stage": "complete", "package": package_name,
        "verdict": verdict, "scan": scan_result, "sandbox": sandbox_result,
        "message": "Package passed all security checks.",
    }