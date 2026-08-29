import requests

from top_100 import find_closest_match
from sandbox import test_install_in_sandbox


# ============================================================
# PYPI LOOKUP
# ============================================================

def fetch_pypi_metadata(package_name):
    """
    Query PyPI for the requested package.

    Returns:
        found      -> package exists
        not_found  -> package does not exist
        error      -> PyPI could not be reached
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


# ============================================================
# CREATION DATE
# ============================================================

def get_creation_date(metadata):

    if not metadata:
        return None

    releases = metadata.get(
        "releases",
        {}
    )

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
# PACKAGE EXISTENCE CHECK
# ============================================================

def check_package(package_name):
    """
    First security gate.

    The ONLY blocking condition at this stage is:
        package does not exist on PyPI.

    Top-100 similarity is advisory.
    """

    normalized_name = (
        package_name
        .strip()
        .lower()
        .replace("_", "-")
    )

    if not normalized_name:

        return {
            "package": package_name,
            "exists": False,
            "status": "blocked",
            "reason": "empty_package_name",
            "closest_match": None,
            "created": None,
        }

    # --------------------------------------------------------
    # PyPI
    # --------------------------------------------------------

    pypi_result = fetch_pypi_metadata(
        normalized_name
    )

    pypi_status = pypi_result["status"]
    metadata = pypi_result["metadata"]

    # --------------------------------------------------------
    # PyPI ERROR
    # --------------------------------------------------------

    if pypi_status == "error":

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
    # PACKAGE DOES NOT EXIST
    # --------------------------------------------------------

    if pypi_status == "not_found":

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
    # PACKAGE EXISTS
    # --------------------------------------------------------

    closest = find_closest_match(
        package_name
    )

    return {
        "package": package_name,
        "exists": True,
        "status": "exists",
        "reason": "package_exists",
        "closest_match": closest,
        "created": get_creation_date(metadata),
    }


# ============================================================
# MAIN SECURITY GATEWAY
# ============================================================

def run_security_check(package_name):
    """
    GhostPkg's complete package security pipeline.

    PIPELINE:

        PyPI existence
              ↓
        Does not exist → BLOCK
              ↓
            Exists
              ↓
          Docker
          /    \
       FAIL    PASS
        ↓        ↓
      BLOCK    APPROVE
    """

    # ========================================================
    # STAGE 1 — PYPI
    # ========================================================

    pypi_result = check_package(
        package_name
    )

    # --------------------------------------------------------
    # PyPI lookup failed
    # --------------------------------------------------------

    if pypi_result["status"] == "unknown":

        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": pypi_result,
            "sandbox": None,
            "message": (
                "Unable to verify package existence "
                "because PyPI lookup failed."
            )
        }

    # --------------------------------------------------------
    # Package does not exist
    # --------------------------------------------------------

    if not pypi_result["exists"]:

        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": pypi_result,
            "sandbox": None,
            "message": (
                "Package does not exist on PyPI."
            )
        }

    # ========================================================
    # STAGE 2 — DOCKER
    # ========================================================

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
            "verdict": pypi_result,
            "sandbox": sandbox_result,
            "message": (
                "Package failed Docker sandbox testing."
            )
        }

    # ========================================================
    # STAGE 3 — APPROVED
    # ========================================================

    return {
        "success": True,
        "stage": "complete",
        "package": package_name,
        "verdict": pypi_result,
        "sandbox": sandbox_result,
        "message": (
            "Package exists on PyPI and passed "
            "Docker sandbox testing."
        )
    }


# ============================================================
# COMMAND LINE INTERFACE
# ============================================================

def install(package_name):

    print("=" * 60)
    print("              GHOSTPKG SAFE-PIP")
    print("=" * 60)

    print(
        f"\n📦 Requested package: {package_name}"
    )

    # ========================================================
    # PYPI
    # ========================================================

    print("\n🔍 PYPI PACKAGE CHECK")
    print("-" * 40)

    verdict = check_package(
        package_name
    )

    print(
        f"Package:       {verdict['package']}"
    )

    print(
        f"PyPI exists:   {verdict['exists']}"
    )

    print(
        f"Reason:        {verdict['reason']}"
    )

    print(
        f"Closest match: {verdict['closest_match']}"
    )

    if verdict["created"]:

        print(
            f"First published: {verdict['created']}"
        )

    # ========================================================
    # PYPI ERROR
    # ========================================================

    if verdict["status"] == "unknown":

        print("\n⚠️ PYPI LOOKUP FAILED")
        print("-" * 40)

        print(
            "Could not determine whether "
            "the package exists."
        )

        print("=" * 60)

        return False

    # ========================================================
    # DOES NOT EXIST
    # ========================================================

    if not verdict["exists"]:

        print("\n🚨 FINAL VERDICT")
        print("-" * 40)

        print("🛑 BLOCKED")

        print(
            f"Package '{package_name}' "
            "does not exist on PyPI."
        )

        if verdict["closest_match"]:

            print(
                f"💡 Did you mean "
                f"'{verdict['closest_match']}'?"
            )

        print("=" * 60)

        return False

    # ========================================================
    # EXISTS
    # ========================================================

    print("\n✅ PACKAGE EXISTS ON PYPI")
    print("-" * 40)

    if verdict["closest_match"]:

        print(
            f"⚠️ Similar to: "
            f"'{verdict['closest_match']}'"
        )

        print(
            "Similarity warning is advisory only."
        )

    else:

        print(
            "Package passed the existence check."
        )

    # ========================================================
    # DOCKER
    # ========================================================

    print("\n🧪 DETONATION CHAMBER")
    print("-" * 40)

    print(
        "Package exists → entering Docker sandbox..."
    )

    sandbox_result = test_install_in_sandbox(
        package_name
    )

    print(
        f"\nStatus:    {sandbox_result['status']}"
    )

    print(
        f"Exit code: {sandbox_result['exit_code']}"
    )

    if sandbox_result["stdout"]:

        print("\nSTDOUT:")
        print(sandbox_result["stdout"])

    if sandbox_result["stderr"]:

        print("\nSTDERR:")
        print(sandbox_result["stderr"])

    # ========================================================
    # DOCKER FAILED
    # ========================================================

    if not sandbox_result["success"]:

        print("\n🚨 FINAL VERDICT")
        print("-" * 40)

        print("🛑 BLOCKED")

        print(
            f"'{package_name}' failed "
            "Docker sandbox testing."
        )

        print("=" * 60)

        return False

    # ========================================================
    # APPROVED
    # ========================================================

    print("\n✅ FINAL VERDICT")
    print("-" * 40)

    print("PACKAGE APPROVED")

    print(
        f"'{package_name}' exists on PyPI "
        "and passed Docker sandbox testing."
    )

    print("=" * 60)

    return True
