import requests

from top_100 import find_closest_match
from sandbox import test_install_in_sandbox


# ============================================================
# PYPI
# ============================================================

def normalize_name(package_name):
    return (
        package_name
        .strip()
        .lower()
        .replace("_", "-")
    )


def fetch_pypi_metadata(package_name):
    """
    Check whether a package exists on PyPI.

    Returns:
        found
        not_found
        error
    """

    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = requests.get(
            url,
            timeout=5
        )

        if response.status_code == 200:
            return {
                "status": "found",
                "metadata": response.json()
            }

        if response.status_code == 404:
            return {
                "status": "not_found",
                "metadata": None
            }

        return {
            "status": "error",
            "metadata": None
        }

    except requests.RequestException:
        return {
            "status": "error",
            "metadata": None
        }


def get_creation_date(metadata):
    """Return the earliest publication date of the package."""

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
    Check package existence on PyPI.

    IMPORTANT:
    Top-100 similarity is ONLY a spelling/suggestion feature.

    It does NOT block an existing package.
    """

    normalized = normalize_name(package_name)

    # --------------------------------------------------------
    # Empty input
    # --------------------------------------------------------

    if not normalized:

        return {
            "package": package_name,
            "exists": False,
            "status": "blocked",
            "reason": "empty_package_name",
            "closest_match": None,
            "created": None,
        }

    # --------------------------------------------------------
    # Query PyPI
    # --------------------------------------------------------

    result = fetch_pypi_metadata(
        normalized
    )

    # --------------------------------------------------------
    # PyPI lookup failed
    # --------------------------------------------------------

    if result["status"] == "error":

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

    if result["status"] == "not_found":

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

    metadata = result["metadata"]

    return {
        "package": package_name,
        "exists": True,
        "status": "exists",
        "reason": "package_exists",
        "closest_match": find_closest_match(
            package_name
        ),
        "created": get_creation_date(
            metadata
        ),
    }


# ============================================================
# SECURITY PIPELINE
# ============================================================

def run_security_check(package_name):
    """
    GhostPkg security pipeline:

        PyPI check
             ↓
        Does it exist?
          /       \
        NO         YES
        ↓           ↓
      BLOCK      Docker
                  ↓
              PASS / FAIL
                  ↓
             APPROVE/BLOCK
    """

    # --------------------------------------------------------
    # STAGE 1 — PYPI
    # --------------------------------------------------------

    verdict = check_package(
        package_name
    )

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
                "because PyPI lookup failed."
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
    # Everything passed
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


# ============================================================
# COMMAND-LINE SAFE-PIP
# ============================================================

def install(package_name):

    print("=" * 60)
    print("              GHOSTPKG SAFE-PIP")
    print("=" * 60)

    print(
        f"\n📦 Requested package: {package_name}"
    )

    # --------------------------------------------------------
    # PYPI
    # --------------------------------------------------------

    print("\n🔍 PYPI PACKAGE CHECK")
    print("-" * 40)

    verdict = check_package(
        package_name
    )

    print(
        f"Package:       {verdict['package']}"
    )

    if verdict["exists"] is True:
        print("PyPI exists:   True")

    elif verdict["exists"] is False:
        print("PyPI exists:   False")

    else:
        print("PyPI exists:   Unknown")

    print(
        f"Reason:        {verdict['reason']}"
    )

    if verdict["closest_match"]:

        print(
            f"Closest match: "
            f"{verdict['closest_match']}"
        )

    if verdict["created"]:

        print(
            f"First published: "
            f"{verdict['created']}"
        )

    # --------------------------------------------------------
    # PYPI BLOCK
    # --------------------------------------------------------

    if verdict["exists"] is False:

        print("\n🚨 FINAL VERDICT")
        print("-" * 40)

        print("🛑 BLOCKED")

        print(
            f"\nPackage '{package_name}' "
            "does not exist on PyPI."
        )

        if verdict["closest_match"]:

            print(
                f"💡 Did you mean "
                f"'{verdict['closest_match']}'?"
            )

        print(
            "\n🐳 Docker chamber: SKIPPED"
        )

        print("=" * 60)

        return False

    # --------------------------------------------------------
    # PYPI ERROR
    # --------------------------------------------------------

    if verdict["exists"] is None:

        print("\n🚨 FINAL VERDICT")
        print("-" * 40)

        print("⚠️ PyPI lookup failed.")

        print(
            "\n🐳 Docker chamber: SKIPPED"
        )

        print("=" * 60)

        return False

    # --------------------------------------------------------
    # EXISTS → DOCKER
    # --------------------------------------------------------

    print("\n✅ PACKAGE EXISTS ON PYPI")

    if verdict["closest_match"]:

        print(
            f"💡 Similar package: "
            f"'{verdict['closest_match']}'"
        )

    print("\n🧪 DETONATION CHAMBER")
    print("-" * 40)

    print(
        "Package exists → entering Docker..."
    )

    sandbox_result = test_install_in_sandbox(
        package_name
    )

    print(
        f"Status:    "
        f"{sandbox_result['status']}"
    )

    print(
        f"Exit code: "
        f"{sandbox_result['exit_code']}"
    )

    if sandbox_result["stdout"]:

        print("\nSTDOUT:")
        print(sandbox_result["stdout"])

    if sandbox_result["stderr"]:

        print("\nSTDERR:")
        print(sandbox_result["stderr"])

    # --------------------------------------------------------
    # DOCKER BLOCK
    # --------------------------------------------------------

    if not sandbox_result["success"]:

        print("\n🚨 FINAL VERDICT")
        print("-" * 40)

        print("🛑 BLOCKED")

        print(
            f"\n'{package_name}' failed "
            "Docker sandbox testing."
        )

        print("=" * 60)

        return False

    # --------------------------------------------------------
    # APPROVED
    # --------------------------------------------------------

    print("\n✅ FINAL VERDICT")
    print("-" * 40)

    print("PACKAGE APPROVED")

    print(
        f"\n'{package_name}' exists on PyPI "
        "and passed Docker sandbox testing."
    )

    print("=" * 60)

    return True
