import difflib
import requests


# ============================================================
# TOP PACKAGES
# ============================================================
# This is NOT a whitelist.
# It is only used for:
# - typo detection
# - similarity suggestions
# - helping identify likely hallucinations
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


# ============================================================
# NORMALIZE PACKAGE NAME
# ============================================================

def normalize_name(package_name):
    return package_name.strip().lower().replace("_", "-")


# ============================================================
# PYPI LOOKUP
# ============================================================

def fetch_pypi_metadata(package_name):
    """
    Check whether a package exists on PyPI.

    Returns:
        {
            "status": "found" | "not_found" | "error",
            "metadata": dict | None
        }
    """

    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = requests.get(url, timeout=5)

        # Package exists
        if response.status_code == 200:
            return {
                "status": "found",
                "metadata": response.json()
            }

        # Package genuinely does not exist
        if response.status_code == 404:
            return {
                "status": "not_found",
                "metadata": None
            }

        # Unexpected PyPI response
        return {
            "status": "error",
            "metadata": None
        }

    except requests.RequestException:
        # Network/DNS/timeout problem.
        # Do NOT claim that the package doesn't exist.
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

    all_dates = []

    for version_files in releases.values():

        for file_info in version_files:

            upload_time = file_info.get("upload_time")

            if upload_time:
                all_dates.append(upload_time)

    if not all_dates:
        return None

    return min(all_dates)


# ============================================================
# CLOSEST PACKAGE
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

    if matches:
        return matches[0]

    return None


# ============================================================
# MAIN CHECK
# ============================================================

def check_package(package_name):

    normalized_input = normalize_name(package_name)

    # --------------------------------------------------------
    # Empty input
    # --------------------------------------------------------

    if not normalized_input:

        return {
            "package": package_name,
            "status": "blocked",
            "reason": "empty_input",
            "closest_match": None,
            "pypi_exists": False,
            "pypi_status": "not_found",
            "created": None,
        }

    # --------------------------------------------------------
    # PyPI lookup
    # --------------------------------------------------------

    pypi_result = fetch_pypi_metadata(normalized_input)

    pypi_status = pypi_result["status"]
    metadata = pypi_result["metadata"]

    exists = pypi_status == "found"

    # --------------------------------------------------------
    # Top 100 similarity
    # --------------------------------------------------------

    closest = find_closest_match(package_name)

    # Do not show the package itself as a typo match.
    if closest == normalized_input:
        closest = None

    # --------------------------------------------------------
    # Creation date
    # --------------------------------------------------------

    created = (
        get_creation_date(metadata)
        if exists
        else None
    )

    # ========================================================
    # DECISION
    # ========================================================

    # PyPI lookup failed
    if pypi_status == "error":

        status = "unknown"
        reason = "pypi_lookup_failed"

    # Package does not exist
    elif pypi_status == "not_found":

        status = "blocked"
        reason = "package_not_found"

    # Package exists
    else:

        # Similarity is ADVISORY only.
        # Existing packages ALWAYS continue to Docker.
        if closest is not None:

            status = "suspicious"
            reason = "possible_typo"

        else:

            status = "safe"
            reason = "package_exists"

    return {
        "package": package_name,
        "status": status,
        "reason": reason,
        "closest_match": closest,
        "pypi_exists": exists,
        "pypi_status": pypi_status,
        "created": created,
    }


# ============================================================
# MANUAL TEST
# ============================================================

if __name__ == "__main__":

    for name in [
        "requests",
        "numpy",
        "numpyy",
        "requests-http-parse"
    ]:

        print(check_package(name))
