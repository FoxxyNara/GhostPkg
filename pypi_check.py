import json
import re
import requests


def normalize_name(package_name: str) -> str:
    """Normalize package names according to PyPI standards (PEP 503)."""
    if not package_name:
        return ""
    return re.sub(r"[-_.]+", "-", package_name.strip().lower())


def fetch_pypi_metadata(package_name: str) -> dict:
    """Check live on PyPI to see if a package exists and fetch metadata."""
    normalized = normalize_name(package_name)
    if not normalized:
        return {
            "status": "empty_input",
            "metadata": None,
        }

    url = f"https://pypi.org/pypi/{normalized}/json"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            return {
                "status": "found",
                "metadata": response.json(),
            }

        if response.status_code == 404:
            return {
                "status": "not_found",
                "metadata": None,
            }

        return {
            "status": "error",
            "metadata": None,
        }

    except (requests.RequestException, ValueError, json.JSONDecodeError):
        return {
            "status": "error",
            "metadata": None,
        }


def get_creation_date(metadata: dict | None) -> str | None:
    """Find the earliest publication date of the package from metadata."""
    if not metadata or not isinstance(metadata.get("releases"), dict):
        return None

    dates = []
    for version_files in metadata["releases"].values():
        if isinstance(version_files, list):
            for file_info in version_files:
                if isinstance(file_info, dict) and file_info.get("upload_time"):
                    dates.append(file_info["upload_time"])

    return min(dates) if dates else None


def check_pypi_exists(package_name: str) -> dict:
    """Primary check to determine if a package exists on PyPI."""
    normalized = normalize_name(package_name)

    if not normalized:
        return {
            "package": package_name,
            "exists": False,
            "status": "blocked",
            "reason": "empty_package_name",
            "created": None,
        }

    pypi_result = fetch_pypi_metadata(normalized)

    if pypi_result["status"] == "error":
        return {
            "package": package_name,
            "exists": None,
            "status": "unknown",
            "reason": "pypi_lookup_failed",
            "created": None,
        }

    if pypi_result["status"] == "not_found":
        return {
            "package": package_name,
            "exists": False,
            "status": "blocked",
            "reason": "package_not_found",
            "created": None,
        }

    metadata = pypi_result["metadata"]

    return {
        "package": package_name,
        "exists": True,
        "status": "exists",
        "reason": "package_exists",
        "created": get_creation_date(metadata),
    }


if __name__ == "__main__":
    test_packages = [
        "requests",
        "numpy",
        "nonexistent-package-xyz-12345",
    ]

    print("=" * 60)
    print("                PYPI CHECK VERIFICATION")
    print("=" * 60)

    for package in test_packages:
        verdict = check_pypi_exists(package)
        print(f"\nPackage: {package}")
        print(f"Exists: {verdict['exists']} | Status: {verdict['status']}")
