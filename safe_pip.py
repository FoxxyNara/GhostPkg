import requests

from top_100 import find_closest_match
from sandbox import test_install_in_sandbox


# ============================================================
# PACKAGE NORMALIZATION
# ============================================================

def normalize_name(package_name):
    return (
        package_name
        .strip()
        .lower()
        .replace("_", "-")
    )


# ============================================================
# PYPI
# ============================================================

def fetch_pypi_metadata(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = requests.get(
            url,
            timeout=5,
        )

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

    except requests.RequestException:
        return {
            "status": "error",
            "metadata": None,
        }


def get_creation_date(metadata):
    if not metadata:
        return None

    releases = metadata.get("releases", {})
    dates = []

    for version_files in releases.values():
        for file_info in version_files:

            upload_time = file_info.get(
                "upload_time"
            )

            if upload_time:
                dates.append(upload_time)

    if not dates:
        return None

    return min(dates)


# ============================================================
# PACKAGE CHECK
# ============================================================

def check_package(package_name):
    """
    PyPI is the first security gate.

    Rules:

    1. Empty package → BLOCK
    2. PyPI lookup failure → UNKNOWN / BLOCK
    3. Package doesn't exist → BLOCK
    4. Package exists → proceed to Docker

    Top-100 is ONLY a suggestion mechanism.
    """

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

    # --------------------------------------------------------
    # PyPI lookup error
    # --------------------------------------------------------

    if pypi_result["status"] == "error":

        return {
            "package": package_name,
            "exists": None,
            "status": "unknown",
            "reason": "pypi_lookup_failed",
            "closest_match": find_closest_match(
                package_name
            ),
            "created": None,
        }

    # --------------------------------------------------------
    # Package doesn't exist
    # --------------------------------------------------------

    if pypi_result["status"] == "not_found":

        return {
            "package": package_name,
            "exists": False,
            "status": "blocked",
            "reason": "package_not_found",
            "closest_match": find_closest_match(
                package_name
            ),
            "created": None,
        }

    # --------------------------------------------------------
    # Package exists
    # --------------------------------------------------------

    metadata = pypi_result["metadata"]

    return {
        "package": package_name,
        "exists": True,
        "status": "exists",
        "reason": "package_exists",
        "closest_match": find_closest_match(
            package_name
        ),
        "created": get_creation_date(metadata),
    }


# ============================================================
# SECURITY PIPELINE
# ============================================================

def run_security_check(package_name):
    """
    GhostPkg pipeline:

        PyPI
          ↓
        EXISTS?
        /     \
      NO       YES
      ↓         ↓
    BLOCK     Docker
                ↓
             PASS/FAIL
    """

    verdict = check_package(package_name)

    # --------------------------------------------------------
    # PyPI lookup failed
    # --------------------------------------------------------

    if verdict["status"] == "unknown":

        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": verdict,
            "sandbox": None,
            "message": (
                "Unable to verify package existence "
                "because the PyPI lookup failed."
            ),
        }

    # --------------------------------------------------------
    # Package doesn't exist
    # --------------------------------------------------------

    if verdict["exists"] is False:

        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": verdict,
            "sandbox": None,
            "message": (
                "Package does not exist on PyPI."
            ),
        }

    # --------------------------------------------------------
    # Package exists → Docker
    # --------------------------------------------------------

    sandbox_result = test_install_in_sandbox(
        package_name
    )

    # --------------------------------------------------------
    # Docker failed
    # --------------------------------------------------------

    if not sandbox_result["success"]:

        return {
            "success": False,
            "stage": "sandbox",
            "package": package_name,
            "verdict": verdict,
            "sandbox": sandbox_result,
            "message": (
                "Package failed Docker "
                "sandbox testing."
            ),
        }

    # --------------------------------------------------------
    # Approved
    # --------------------------------------------------------

    return {
        "success": True,
        "stage": "complete",
        "package": package_name,
        "verdict": verdict,
        "sandbox": sandbox_result,
        "message": (
            "Package exists on PyPI and passed "
            "Docker sandbox testing."
        ),
    }


if __name__ == "__main__":

    for package in [
        "numpy",
        "numpyy",
        "requests-http-parse",
    ]:
        print(
            run_security_check(package)
        )
