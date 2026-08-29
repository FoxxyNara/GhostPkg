import difflib
import requests

from sandbox import test_install_in_sandbox

# ============================================================
# TOP 100 PACKAGES — used ONLY for typo/spelling suggestions.
# It does NOT decide safety, block anything, or replace the
# real PyPI check or the Docker sandbox test below.
# ============================================================

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
    "redis", "pymongo", "psycopg2", "mysqlclient", "sqlite3",
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
    """NumPy -> numpy, my_package -> my-package, etc."""
    return package_name.strip().lower().replace("_", "-")


def find_closest_match(package_name, cutoff=0.8):
    """
    Suggestion-only spelling check against TOP_100_PACKAGES.
    Returns a package name if suspiciously close, else None.
    Never returns the package's own name as its own "closest match".
    """
    normalized_input = normalize_name(package_name)
    normalized_packages = [normalize_name(p) for p in TOP_100_PACKAGES]
    matches = difflib.get_close_matches(normalized_input, normalized_packages, n=1, cutoff=cutoff)
    if not matches:
        return None
    closest = matches[0]
    if closest == normalized_input:
        return None
    return closest


# ============================================================
# PYPI LOOKUP
# ============================================================

def fetch_pypi_metadata(package_name):
    """
    Query PyPI for the requested package.
    Returns {"status": "found"|"not_found"|"error", "metadata": dict|None}
    """
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


def get_creation_date(metadata):
    """Earliest upload date across every version ever published."""
    if not metadata:
        return None
    releases = metadata.get("releases", {})
    dates = []
    for version_files in releases.values():
        for file_info in version_files:
            upload_time = file_info.get("upload_time")
            if upload_time:
                dates.append(upload_time)
    if not dates:
        return None
    return min(dates)


# ============================================================
# PACKAGE CHECK — the only blocking condition here is
# "does not exist on PyPI". Typo similarity is advisory only.
# ============================================================

def check_package(package_name):
    normalized = normalize_name(package_name)

    if not normalized:
        return {
            "package": package_name,
            "exists": False,
            "status": "blocked",
            "reason": "empty_package_name",
            "closest_match": None,
            "created": None,
        }

    result = fetch_pypi_metadata(normalized)

    if result["status"] == "error":
        return {
            "package": package_name,
            "exists": None,
            "status": "unknown",
            "reason": "pypi_lookup_failed",
            "closest_match": find_closest_match(package_name),
            "created": None,
        }

    if result["status"] == "not_found":
        return {
            "package": package_name,
            "exists": False,
            "status": "blocked",
            "reason": "package_not_found",
            "closest_match": find_closest_match(package_name),
            "created": None,
        }

    return {
        "package": package_name,
        "exists": True,
        "status": "exists",
        "reason": "package_exists",
        "closest_match": find_closest_match(package_name),
        "created": get_creation_date(result["metadata"]),
    }


# ============================================================
# FULL SECURITY PIPELINE — PyPI check, then Docker sandbox.
# Only "does not exist" skips the sandbox entirely.
# ============================================================

def run_security_check(package_name):
    verdict = check_package(package_name)

    if verdict["status"] == "unknown":
        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": verdict,
            "sandbox": None,
            "message": "Unable to verify package existence because PyPI lookup failed.",
        }

    if verdict["exists"] is False:
        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": verdict,
            "sandbox": None,
            "message": "Package does not exist on PyPI.",
        }

    sandbox_result = test_install_in_sandbox(package_name)

    if not sandbox_result["success"]:
        return {
            "success": False,
            "stage": "sandbox",
            "package": package_name,
            "verdict": verdict,
            "sandbox": sandbox_result,
            "message": "Package failed Docker sandbox testing.",
        }

    return {
        "success": True,
        "stage": "complete",
        "package": package_name,
        "verdict": verdict,
        "sandbox": sandbox_result,
        "message": "Package exists on PyPI and passed Docker sandbox testing.",
    }


if __name__ == "__main__":
    for name in ["numpy", "numpyy", "requests-http-parse", ""]:
        print(name, "->", check_package(name))
