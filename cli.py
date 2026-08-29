import requests

from top_100 import find_closest_match
from sandbox import test_install_in_sandbox


def fetch_pypi_metadata(package_name):
    """Check whether the package exists on PyPI."""

    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            return response.json()

        if response.status_code == 404:
            return None

        return None

    except requests.RequestException:
        return None


def get_creation_date(metadata):
    """Get the earliest known publication date."""

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
    Check package existence on PyPI.

    Top-100 is ONLY used for spelling/similarity suggestions.
    It does NOT determine whether an existing package is blocked.
    """

    normalized = (
        package_name
        .strip()
        .lower()
        .replace("_", "-")
    )

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
    # Check PyPI
    # --------------------------------------------------------

    metadata = fetch_pypi_metadata(normalized)

    # --------------------------------------------------------
    # Package does NOT exist
    # --------------------------------------------------------

    if metadata is None:

        return {
            "package": package_name,
            "exists": False,
            "status": "blocked",
            "reason": "package_not_found",
            "closest_match": find_closest_match(package_name),
            "created": None,
        }

    # --------------------------------------------------------
    # Package DOES exist
    #
    # IMPORTANT:
    # Even if it resembles a Top-100 package,
    # it is NOT blocked here.
    # It proceeds to Docker.
    # --------------------------------------------------------

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
    GhostPkg security pipeline:

        1. Check PyPI existence
        2. If nonexistent -> BLOCK
        3. If nonexistent -> show Top-100 suggestion
        4. If exists -> Docker sandbox
        5. Docker PASS -> APPROVE
        6. Docker FAIL -> BLOCK
    """

    # ========================================================
    # STAGE 1 — PYPI
    # ========================================================

    verdict = check_package(package_name)

    # --------------------------------------------------------
    # Package doesn't exist
    # --------------------------------------------------------

    if not verdict["exists"]:

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
            "verdict": verdict,
            "sandbox": sandbox_result,
            "message": (
                "Package failed Docker sandbox testing."
            ),
        }

    # ========================================================
    # STAGE 3 — APPROVED
    # ========================================================

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


def install(package_name):
    """
    CLI-facing Safe-Pip command.
    """

    print("=" * 60)
    print("              GHOSTPKG SAFE-PIP")
    print("=" * 60)

    print(f"\n📦 Requested package: {package_name}")

    # ========================================================
    # PYPI CHECK
    # ========================================================

    print("\n🔍 PYPI PACKAGE CHECK")
    print("-" * 40)

    verdict = check_package(package_name)

    print(f"Package:       {verdict['package']}")
    print(f"PyPI exists:   {verdict['exists']}")
    print(f"Reason:        {verdict['reason']}")

    if verdict["closest_match"]:
        print(
            f"Closest match: {verdict['closest_match']}"
        )
    else:
        print("Closest match: None")

    if verdict["created"]:
        print(
            f"First published: {verdict['created']}"
        )

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

        print("\n🐳 Docker chamber: SKIPPED")

        print("=" * 60)

        return False

    # ========================================================
    # EXISTS → DOCKER
    # ========================================================

    print("\n✅ PACKAGE EXISTS ON PYPI")

    if verdict["closest_match"]:
        print(
            f"💡 Similar package suggestion: "
            f"'{verdict['closest_match']}'"
        )

    print("\n🧪 DETONATION CHAMBER")
    print("-" * 40)

    print(
        "Package exists → entering Docker sandbox..."
    )

    sandbox_result = test_install_in_sandbox(
        package_name
    )

    print(
        f"Status:    {sandbox_result['status']}"
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
    # DOCKER FAILURE
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
