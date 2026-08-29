import difflib


# ============================================================
# TOP 100 PYTHON PACKAGES
# ============================================================
# This list is ONLY used for spelling / typo suggestions.
#
# It does NOT:
#   - decide whether a package is safe
#   - block packages
#   - replace PyPI verification
#   - replace Docker sandbox testing
# ============================================================

TOP_100_PACKAGES = [
    "requests",
    "urllib3",
    "boto3",
    "botocore",
    "setuptools",
    "pip",
    "wheel",

    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "scikit-learn",
    "seaborn",

    "django",
    "flask",
    "fastapi",
    "starlette",
    "uvicorn",
    "gunicorn",

    "sqlalchemy",
    "pydantic",
    "jinja2",
    "werkzeug",
    "click",
    "typer",

    "pytest",
    "tox",
    "nose",
    "coverage",
    "mock",

    "pyyaml",
    "toml",
    "python-dotenv",
    "attrs",
    "packaging",

    "certifi",
    "charset-normalizer",
    "idna",
    "six",
    "python-dateutil",
    "pytz",
    "tzdata",

    "cryptography",
    "pyjwt",
    "bcrypt",

    "pillow",
    "opencv-python",
    "imageio",
    "scikit-image",

    "beautifulsoup4",
    "lxml",
    "html5lib",
    "soupsieve",

    "selenium",
    "playwright",
    "scrapy",

    "tensorflow",
    "torch",
    "torchvision",
    "keras",
    "transformers",

    "huggingface-hub",
    "tokenizers",
    "sentencepiece",

    "openai",
    "anthropic",
    "langchain",
    "langchain-core",

    "boto",
    "azure-storage-blob",
    "google-cloud-storage",

    "redis",
    "pymongo",
    "psycopg2",
    "mysqlclient",
    "sqlite3",

    "celery",
    "kombu",
    "billiard",

    "gevent",
    "eventlet",
    "greenlet",

    "tqdm",
    "rich",
    "colorama",
    "tabulate",

    "loguru",
    "structlog",

    "pyparsing",
    "regex",
    "markupsafe",

    "protobuf",
    "grpcio",
    "googleapis-common-protos",

    "aiohttp",
    "httpx",
    "websockets",

    "flake8",
    "black",
    "isort",
    "mypy",
    "pylint",

    "sphinx",
    "mkdocs",
]


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_name(package_name):
    """
    Normalize package names for comparison.

    Example:
        NumPy       -> numpy
        numpy       -> numpy
        my_package  -> my-package
    """

    return (
        package_name
        .strip()
        .lower()
        .replace("_", "-")
    )


# ============================================================
# FIND CLOSEST PACKAGE
# ============================================================

def find_closest_match(
    package_name,
    cutoff=0.8
):
    """
    Find the closest Top-100 package name.

    This is ONLY a suggestion mechanism.

    Returns:
        package name -> if a close match exists
        None         -> if no close match exists
    """

    normalized_input = normalize_name(
        package_name
    )

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

    # Don't suggest the package itself.
    if closest == normalized_input:
        return None

    return closest


# ============================================================
# MANUAL TEST
# ============================================================

if __name__ == "__main__":

    test_packages = [
        "numpy",
        "numpyy",
        "nump",
        "requests",
        "requsts",
        "requests-http-parse",
        "fastapi",
        "fastapy",
    ]

    print("=" * 60)
    print("          GHOSTPKG TOP-100 SPELL CHECK")
    print("=" * 60)

    for package in test_packages:

        match = find_closest_match(package)

        if match:

            print(
                f"{package:<25} -> {match}"
            )

        else:

            print(
                f"{package:<25} -> No suggestion"
            )
