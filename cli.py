import argparse

from pypi_check import check_package
from sandbox import test_install_in_sandbox


# ============================================================
# SECURITY PIPELINE
# ============================================================

def run_security_check(package_name):
    """
    GhostPkg security pipeline.

    1. Check PyPI.
    2. If package does not exist -> BLOCK.
    3. If package exists -> Docker.
    4. Docker failure -> BLOCK.
    5. Docker success -> APPROVE.

    Top-100 similarity is advisory only.
    """

    # --------------------------------------------------------
    # PYPI
    # --------------------------------------------------------

    pypi_result = check_package(package_name)

    # PyPI lookup failed
    if pypi_result["status"] == "unknown":

        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": pypi_result,
            "sandbox": None,
            "message": "PyPI lookup failed."
        }

    # --------------------------------------------------------
    # PACKAGE DOES NOT EXIST
    # --------------------------------------------------------

    if not pypi_result["pypi_exists"]:

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

    # --------------------------------------------------------
    # PACKAGE EXISTS
    # --------------------------------------------------------
    # Even if suspicious, it enters Docker.
    # --------------------------------------------------------

    sandbox_result = test_install_in_sandbox(
        package_name
    )

    # --------------------------------------------------------
    # DOCKER FAILURE
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

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    return {
        "success": True,
        "stage": "complete",
        "package": package_name,
        "verdict": pypi_result,
        "sandbox": sandbox_result,
        "message": (
            "Package passed PyPI verification "
            "and Docker sandbox testing."
        )
    }


# ============================================================
# CLI OUTPUT
# ============================================================

def show_result(package_name):

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

    verdict = check_package(package_name)

    print(
        f"Package:       {verdict['package']}"
    )

    print(
        f"PyPI status:   {verdict['pypi_status']}"
    )

    print(
        f"PyPI exists:   {verdict['pypi_exists']}"
    )

    print(
        f"Status:        {verdict['status']}"
    )

    print(
        f"Reason:        {verdict['reason']}"
    )

    print(
        f"Closest match: {verdict['closest_match']}"
    )

    if verdict.get("created"):

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
            "Could not determine whether the package exists."
        )

        print("=" * 60)

        return False

    # ========================================================
    # PACKAGE DOES NOT EXIST
    # ========================================================

    if not verdict["pypi_exists"]:

        print("\n🚨 FINAL VERDICT")
        print("-" * 40)

        print("🛑 BLOCKED")

        print(
            f"Package '{package_name}' "
            "does not exist on PyPI."
        )

        if verdict.get("closest_match"):

            print(
                f"💡 Did you mean "
                f"'{verdict['closest_match']}'?"
            )

        print("=" * 60)

        return False

    # ========================================================
    # PACKAGE EXISTS
    # ========================================================

    print("\n✅ PACKAGE EXISTS ON PYPI")
    print("-" * 40)

    if verdict["status"] == "suspicious":

        print(
            f"⚠️ Similar to known package: "
            f"'{verdict['closest_match']}'"
        )

        print(
            "Advisory warning only."
        )

    else:

        print(
            "Package exists on PyPI."
        )

    print(
        "\nProceeding to Docker detonation..."
    )

    # ========================================================
    # DOCKER
    # ========================================================

    print("\n🧪 DETONATION CHAMBER")
    print("-" * 40)

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

        print("🛑 SANDBOX FAILED")

        print(
            f"\n'{package_name}' failed "
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


# ============================================================
# COMMAND LINE INTERFACE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        prog="safe-pip",
        description="GhostPkg secure Python package gateway"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    install_parser = subparsers.add_parser(
        "install",
        help="Check and sandbox a package"
    )

    install_parser.add_argument(
        "package",
        help="Package name"
    )

    args = parser.parse_args()

    if args.command == "install":

        success = show_result(
            args.package
        )

        return 0 if success else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
