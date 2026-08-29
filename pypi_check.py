import difflib


# ============================================================
# TOP 100 COMMON PYTHON PACKAGES
#
# Used ONLY for spelling/similarity suggestions.
# This list does NOT determine whether a package is safe.
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
        My_Package -> my-package
        NumPy      -> numpy
    """

    return (
        package_name
        .strip()
        .lower()
        .replace("_", "-")
    )


# ============================================================
# SIMILARITY CHECK
# ============================================================

def find_closest_match(
    package_name,
    cutoff=0.8,
):
    """
    Find the closest common package name.

    IMPORTANT:
    This function only provides a suggestion.

    It does NOT:
      - check PyPI
      - run Docker
      - block packages
      - approve packages
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
        cutoff=cutoff,
    )

    if not matches:
        return None

    closest = matches[0]

    # Don't suggest the package itself.
    if closest == normalized_input:
        return None

    return closest


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_packages = [
        "numpy",
        "numpyy",
        "nump",
        "requests",
        "requsts",
        "requests-http-parse",
    ]

    print("=" * 60)
    print("             GHOSTPKG TOP-100")
    print("=" * 60)

    for package in test_packages:

        suggestion = find_closest_match(
            package
        )

        print(
            f"\n{package}"
            f" → "
            f"{suggestion or 'No suggestion'}"
        )
