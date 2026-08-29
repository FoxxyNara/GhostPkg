import difflib
import requests

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


def fetch_pypi_metadata(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


def get_creation_date(metadata):
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


def find_closest_match(package_name):
    normalized_input = normalize_name(package_name)
    normalized_list = [normalize_name(name) for name in TOP_100_PACKAGES]
    matches = difflib.get_close_matches(normalized_input, normalized_list, n=1, cutoff=0.8)
    if matches:
        return matches[0]
    return None


def check_package(package_name):
    normalized_input = normalize_name(package_name)
    if not normalized_input:
        return {
            "package": package_name,
            "status": "blocked",
            "reason": "empty_input",
            "closest_match": None,
            "pypi_exists": False,
            "created": None,
        }

    normalized_list = [normalize_name(name) for name in TOP_100_PACKAGES]
    metadata = fetch_pypi_metadata(normalized_input)
    exists = metadata is not None
    closest = find_closest_match(package_name)
    created = get_creation_date(metadata) if exists else None

    if normalized_input in normalized_list:
        status, reason = "safe", "ok"
    elif not exists:
        status, reason = "blocked", "unknown_package"
    elif closest is not None and closest != normalized_input:
        status, reason = "suspicious", "typosquat"
    else:
        status, reason = "safe", "ok"

    return {
        "package": package_name,
        "status": status,
        "reason": reason,
        "closest_match": closest,
        "pypi_exists": exists,
        "created": created,
    }


if __name__ == "__main__":
    for name in ["numpy", "numpyy", "requests-http-parse"]:
        print(check_package(name))