import difflib
import requests


# ============================================================
# TOP 100 PACKAGES
# ============================================================
# This list is NOT a whitelist.
# It is only used for:
# - typo detection
# - similarity detection
# - suggesting likely intended packages
# ============================================================

TOP_100_PACKAGES = [
    "requests", "urllib3", "boto3", "botocore", "setuptools", "pip", "wheel",
    "numpy", "pandas", "scipy", "matplotlib", "scikit-learn", "seaborn",
    "django", "flask", "fastapi", "starlette", "uvicorn", "gunicorn",
    "sqlalchemy", "pydantic", "jinja2", "werkzeug", "click", "typer",
    "pytest", "tox", "nose", "coverage", "mock",
    "pyyaml", "toml", "python-dotenv", "attrs", "packaging",
    "certifi", "charset-normalizer", "idna", "six", "python-dateutil",
    "pytz", "tzdata", "cryptography", "pyjwt", "bcrypt",
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
    return package_name.strip().lower().replace("_", "-")


# ============================================================
# PYPI
# ============================================================

def fetch_pypi_metadata(package_name):
    """
    Returns:
        found     -> package exists
        not_found -> package does not exist
        error     -> PyPI could not be reached
    """

    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            return {
                "status": "found",
                "metadata": response.json()
            }

        if response.status_code == 404:
            return {
                "status": "not_found",
                "metadata": None
            }

        return {
            "status": "error",
            "metadata": None
        }

    except requests.RequestException:
        return {
            "status": "error",
            "metadata": None
        }


# ============================================================
# CREATION DATE
# ============================================================

def get_creation_date(metadata):

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
# TOP-100 SIMILARITY
# ============================================================

def find_closest_match(package_name):

    normalized_input = normalize_name(package_name)

    normalized_list = [
        normalize_name(name)
        for name in TOP_100_PACKAGES
    ]

    matches = difflib.get_close_matches(
        normalized_input,
        normalized_list,
        n=1,
        cutoff=0.8
    )

    if not matches:
        return None

    closest = matches[0]

    if closest == normalized_input:
        return None

    return closest


# ============================================================
# PACKAGE CHECK
# ============================================================

def check_package(package_name):

    normalized_input = normalize_name(package_name)

    if not normalized_input:

        return {
            "package": package_name,
            "pypi_exists": False,
            "pypi_status": "not_found",
            "status": "blocked",
            "reason": "empty_input",
            "closest_match": None,
            "created": None,
        }

    # PyPI
    pypi_result = fetch_pypi_metadata(normalized_input)

    pypi_status = pypi_result["status"]
    metadata = pypi_result["metadata"]

    exists = pypi_status == "found"

    # Top-100 similarity
    closest = find_closest_match(package_name)

    # Creation date
    created = (
        get_creation_date(metadata)
        if exists
        else None
    )

    # ========================================================
    # DECISION
    # ========================================================

    if pypi_status == "error":

        status = "unknown"
        reason = "pypi_lookup_failed"

    elif pypi_status == "not_found":

        status = "blocked"
        reason = "package_not_found"

    else:

        # IMPORTANT:
        # A similarity match does NOT block the package.
        if closest:

            status = "suspicious"
            reason = "possible_typo"

        else:

            status = "safe"
            reason = "package_exists"

    return {
        "package": package_name,
        "pypi_exists": exists,
        "pypi_status": pypi_status,
        "status": status,
        "reason": reason,
        "closest_match": closest,
        "created": created,
    }


# ============================================================
# MANUAL TEST
# ============================================================

if __name__ == "__main__":

    test_packages = [
        "requests",
        "numpy",
        "numpyy",
        "requests-http-parse"
    ]

    for package in test_packages:

        print(check_package(package))
