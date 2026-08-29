import json
import requests
from sandbox import test_install_in_sandbox
from top_100 import find_closest_match, normalize_name


def fetch_pypi_metadata(package_name: str) -> dict:
    """Check whether the requested package exists on PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"

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
    """Find the earliest publication date of the package."""
    if not metadata or not isinstance(metadata.get("releases"), dict):
        return None

    dates = []
    for version_files in metadata["releases"].values():
        if isinstance(version_files, list):
            for file_info in version_files:
                if isinstance(file_info, dict) and file_info.get("upload_time"):
                    dates.append(file_info["upload_time"])

    if not dates:
        return None

    return min(dates)


def check_package(package_name: str) -> dict:
    """First security gate: check PyPI availability."""
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

    pypi_result = fetch_pypi_metadata(normalized)

    if pypi_result["status"] == "error":
        return {
            "package": package_name,
            "exists": None,
            "status": "unknown",
            "reason": "pypi_lookup_failed",
            "closest_match": find_closest_match(package_name),
            "created": None,
        }

    if pypi_result["status"] == "not_found":
        return {
            "package": package_name,
            "exists": False,
            "status": "blocked",
            "reason": "package_not_found",
            "closest_match": find_closest_match(package_name),
            "created": None,
        }

    metadata = pypi_result["metadata"]

    return {
        "package": package_name,
        "exists": True,
        "status": "exists",
        "reason": "package_exists",
        "closest_match": find_closest_match(package_name),
        "created": get_creation_date(metadata),
    }


def run_security_check(package_name: str) -> dict:
    """GhostPkg security pipeline execution."""
    verdict = check_package(package_name)

    if verdict["status"] == "unknown":
        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": verdict,
            "sandbox": None,
            "message": (
                "Unable to verify package existence because the PyPI lookup failed."
            ),
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
    packages = [
        "requests",
        "numpy",
        "numpyy",
        "requests-http-parse",
    ]

    for package in packages:
        print("\n" + "=" * 60)
        print(f"Testing: {package}")
        result = run_security_check(package)
        print(result)
