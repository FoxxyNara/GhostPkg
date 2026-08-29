import difflib


# ============================================================
# TOP 100 PYTHON PACKAGES
# ============================================================
# This is NOT a whitelist.
#
# It is used only for:
# - typo detection
# - similarity detection
# - "Did you mean?" suggestions
#
# A package NOT in this list is still allowed to proceed
# if it exists on PyPI.
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
    """
    Normalize a Python package name for comparison.
    """

    return (
        package_name
        .strip()
        .lower()
        .replace("_", "-")
    )


def find_closest_match(package_name, cutoff=0.8):
    """
    Find the closest Top-100 package name.

    Returns:
        package name if a close match exists
        None otherwise
    """

    normalized_input = normalize_name(package_name)

    normalized_packages = [
        normalize_name(package)
        for package in TOP_100_PACKAGES
    ]

    matches = difflib.get_close_matches(
        normalized_input,
        normalized_packages,
        n=1,
        cutoff=cutoff
    )

    if not matches:
        return None

    closest = matches[0]

    # Don't report the package itself as a typo.
    if closest == normalized_input:
        return None

    return closest


if __name__ == "__main__":

    tests = [
        "requests",
        "request",
        "numpyy",
        "flassk",
        "random-new-package"
    ]

    for package in tests:

        print(
            f"{package:25} -> "
            f"{find_closest_match(package)}"
        )
