import sys

from pypi_check import check_package
from sandbox import test_install_in_sandbox


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

    print(f"Package:       {verdict['package']}")
    print(f"Status:        {verdict['status']}")
    print(f"Reason:        {verdict['reason']}")
    print(f"Closest match: {verdict['closest_match']}")
    print(f"PyPI exists:   {verdict['pypi_exists']}")

    if verdict["created"]:
        print(f"First published: {verdict['created']}")

    # ======================================================
    # BLOCK STATIC THREATS
    # ======================================================

    if verdict["status"] in ("blocked", "suspicious"):

        print("\n🚨 FINAL VERDICT")
        print("-" * 40)

        print("🛑 BLOCKED")

        if verdict["reason"] == "typosquat":
            print(
                f"Suspicious package. "
                f"Did you mean '{verdict['closest_match']}'?"
            )
        else:
            print(
                f"Package '{package_name}' failed "
                "static security checks."
            )

        print("=" * 60)

        return False

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