import difflib
import re

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


def normalize_name(package_name: str) -> str:
    """Normalize package names according to PEP 503."""
    if not package_name:
        return ""
    return re.sub(r"[-_.]+", "-", package_name.strip().lower())


# Pre-compute mapping of normalized names to original canonical names
NORMALIZED_TOP_100 = {normalize_name(pkg): pkg for pkg in TOP_100_PACKAGES}


def find_closest_match(package_name: str, cutoff: float = 0.8) -> str | None:
    """Find the closest common package name."""
    normalized_input = normalize_name(package_name)
    if not normalized_input:
        return None

    matches = difflib.get_close_matches(
        normalized_input,
        list(NORMALIZED_TOP_100.keys()),
        n=1,
        cutoff=cutoff,
    )

    if not matches:
        return None

    closest = matches[0]

    # Don't suggest the package itself
    if closest == normalized_input:
        return None

    return NORMALIZED_TOP_100[closest]


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
    print("               GHOSTPKG TOP-100")
    print("=" * 60)

    for package in test_packages:
        suggestion = find_closest_match(package)
        print(f"\n{package} → {suggestion or 'No suggestion'}")
