import requests

from top_100 import find_closest_match
from sandbox import test_install_in_sandbox


def normalize_name(package_name):
    return package_name.strip().lower().replace("_", "-")


def fetch_pypi_metadata(package_name):
    """Ask PyPI if this package exists, and get its full data if so."""
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
    """Find the earliest upload date across all versions ever published."""
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


def check_package(package_name):
    """
    First security gate.
    The ONLY blocking condition here is: package does not exist on PyPI.
    Typo/similarity info is advisory only — shown, but doesn't block.
    """
    normalized_name = normalize_name(package_name)

    if not normalized_name:
        return {
            "package": package_name,
            "exists": False,
            "status": "blocked",
            "reason": "empty_package_name",
            "closest_match": None,
            "created": None,
        }

    pypi_result = fetch_pypi_metadata(normalized_name)
    pypi_status = pypi_result["status"]
    metadata = pypi_result["metadata"]

    if pypi_status == "error":
        return {
            "package": package_name,
            "exists": None,
            "status": "unknown",
            "reason": "pypi_lookup_failed",
            "closest_match": find_closest_match(package_name),
            "created": None,
        }

    if pypi_status == "not_found":
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
        "created": get_creation_date(metadata),
    }


def run_security_check(package_name):
    """
    Full pipeline: PyPI existence check -> Docker sandbox test.
    Only packages that don't exist on PyPI skip the sandbox entirely.
    """
    pypi_result = check_package(package_name)

    if pypi_result["status"] == "unknown":
        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": pypi_result,
            "sandbox": None,
            "message": "Unable to verify package existence because PyPI lookup failed.",
        }

    if not pypi_result["exists"]:
        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": pypi_result,
            "sandbox": None,
            "message": "Package does not exist on PyPI.",
        }

    sandbox_result = test_install_in_sandbox(package_name)

    if not sandbox_result["success"]:
        return {
            "success": False,
            "stage": "sandbox",
            "package": package_name,
            "verdict": pypi_result,
            "sandbox": sandbox_result,
            "message": "Package failed Docker sandbox testing.",
        }

    return {
        "success": True,
        "stage": "complete",
        "package": package_name,
        "verdict": pypi_result,
        "sandbox": sandbox_result,
        "message": "Package exists on PyPI and passed Docker sandbox testing.",
    }


if __name__ == "__main__":
    for name in ["numpy", "numpyy", "requests-http-parse"]:
        print(check_package(name))
