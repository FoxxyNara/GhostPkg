import sys

from pypi_check import check_package
from sandbox import test_install_in_sandbox


def run_security_check(package_name):
    """
    Run the complete GhostPkg security pipeline.

    Pipeline:
        1. Static PyPI analysis
        2. Block packages that do not exist
        3. Send existing packages (safe OR suspicious) to Docker
        4. Approve only if Docker installation succeeds

    Returns a structured result for the AI agent.
    """

    # ======================================================
    # STATIC ANALYSIS
    # ======================================================

    static_result = check_package(package_name)

    # ------------------------------------------------------
    # BLOCK: Package does not exist on PyPI
    # ------------------------------------------------------

    if static_result["status"] == "blocked":

        return {
            "success": False,
            "stage": "static",
            "package": package_name,
            "verdict": static_result,
            "sandbox": None,
        }

    # ======================================================
    # DOCKER DETONATION
    # ======================================================

    sandbox_result = test_install_in_sandbox(package_name)

    # ------------------------------------------------------
    # BLOCK: Docker installation failed
    # ------------------------------------------------------

    if not sandbox_result["success"]:

        return {
            "success": False,
            "stage": "sandbox",
            "package": package_name,
            "verdict": static_result,
            "sandbox": sandbox_result,
        }

    # ======================================================
    # APPROVED
    # ======================================================

    return {
        "success": True,
        "stage": "complete",
        "package": package_name,
        "verdict": static_result,
        "sandbox": sandbox_result,
    }


def install(package_name):

    print("=" * 60)
    print("              GHOSTPKG SAFE-PIP")
    print("=" * 60)

    print(f"\n📦 Requested package: {package_name}")

    # ======================================================
    # STATIC ANALYSIS
    # ======================================================

    print("\n🔍 STATIC ANALYSIS")
    print("-" * 40)

    verdict = check_package(package_name)

    print(f"Package:          {verdict['package']}")
    print(f"Status:           {verdict['status']}")
    print(f"Reason:           {verdict['reason']}")
    print(f"Closest match:    {verdict['closest_match']}")
    print(f"PyPI exists:      {verdict['pypi_exists']}")

    if verdict.get("created"):
        print(f"First published:  {verdict['created']}")

    # ======================================================
    # BLOCK NONEXISTENT PACKAGE
    # ======================================================

    if verdict["status"] == "blocked":

        print("\n🚨 FINAL VERDICT")
        print("-" * 40)

        print("🛑 BLOCKED")

        if verdict["reason"] == "unknown_package":

            if verdict["closest_match"]:
                print(
                    f"Package '{package_name}' does not exist on PyPI."
                )
                print(
                    f"Possible intended package: "
                    f"'{verdict['closest_match']}'"
                )
            else:
                print(
                    f"Package '{package_name}' does not exist on PyPI."
                )

        else:
            print(
                f"Package '{package_name}' failed "
                "static security checks."
            )

        print("=" * 60)

        return False

    # ======================================================
    # SUSPICIOUS PACKAGE
    # ======================================================

    if verdict["status"] == "suspicious":

        print("\n⚠️  STATIC WARNING")
        print("-" * 40)

        print(
            f"Package '{package_name}' is suspicious."
        )

        if verdict["closest_match"]:
            print(
                f"Closest known package: "
                f"'{verdict['closest_match']}'"
            )

        print(
            "\nPackage exists on PyPI."
            "\nProceeding to Docker detonation..."
        )

    # ======================================================
    # SAFE PACKAGE
    # ======================================================

    else:

        print("\n✅ STATIC ANALYSIS PASSED")
        print(
            "Package exists and passed the static checks."
        )

    # ======================================================
    # DOCKER DETONATION
    # ======================================================

    print("\n🧪 DETONATION CHAMBER")
    print("-" * 40)

    sandbox_result = test_install_in_sandbox(package_name)

    print(f"Status:    {sandbox_result['status']}")
    print(f"Exit code: {sandbox_result['exit_code']}")

    if sandbox_result["stdout"]:

        print("\nSTDOUT:")
        print(sandbox_result["stdout"])

    if sandbox_result["stderr"]:

        print("\nSTDERR:")
        print(sandbox_result["stderr"])

    # ======================================================
    # SANDBOX FAILURE
    # ======================================================

    if not sandbox_result["success"]:

        print("\n🚨 FINAL VERDICT")
        print("-" * 40)

        print("🛑 SANDBOX FAILED")
        print()
        print(sandbox_result["message"])

        print("=" * 60)

        return False

    # ======================================================
    # APPROVED
    # ======================================================

    print("\n✅ FINAL VERDICT")
    print("-" * 40)

    print("PACKAGE APPROVED")

    if verdict["status"] == "suspicious":

        print(
            f"'{package_name}' was flagged as suspicious "
            "but successfully passed Docker sandbox testing."
        )

    else:

        print(
            f"'{package_name}' passed static analysis "
            "and Docker sandbox testing."
        )

    print("=" * 60)

    return True


def main():

    if len(sys.argv) != 3:

        print("Usage:")
        print("  python ghostpkg.py install <package>")

        return 1

    command = sys.argv[1]
    package_name = sys.argv[2]

    if command != "install":

        print(f"Unknown command: {command}")

        print("Usage:")
        print("  python ghostpkg.py install <package>")

        return 1

    success = install(package_name)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
