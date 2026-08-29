import argparse

from pypi_check import check_package
from sandbox import test_install_in_sandbox

def run_security_check(package_name):
    """
    Run GhostPkg's complete security pipeline and return
    a structured result for other components such as the AI agent.
    """

    static_result = check_package(package_name)

    # Static block
    if static_result["status"] in ("blocked", "suspicious"):
        return {
            "success": False,
            "stage": "static",
            "package": package_name,
            "verdict": static_result,
        }

    # Docker detonation
    sandbox_result = test_install_in_sandbox(package_name)

    if not sandbox_result["success"]:
        return {
            "success": False,
            "stage": "sandbox",
            "package": package_name,
            "verdict": static_result,
            "sandbox": sandbox_result,
        }

    return {
        "success": True,
        "stage": "complete",
        "package": package_name,
        "verdict": static_result,
        "sandbox": sandbox_result,
    }

def show_result(package_name):

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
    # STATIC BLOCK
    # ======================================================

    if verdict["status"] == "blocked":

        print("\n🚨 FINAL VERDICT")
        print("-" * 40)

        print("BLOCKED")
        print(
            f"Package '{package_name}' failed "
            "static security checks."
        )

        return

    # ======================================================
    # SUSPICIOUS PACKAGE
    # ======================================================

    if verdict["status"] == "suspicious":

        print("\n⚠️ SUSPICIOUS PACKAGE")
        print("-" * 40)

        print(
            f"'{package_name}' is suspiciously close to "
            f"'{verdict['closest_match']}'."
        )

        print("\n🚨 FINAL VERDICT")
        print("-" * 40)

        print("BLOCKED")

        return

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

        return

    # ======================================================
    # EVERYTHING PASSED
    # ======================================================

    print("\n✅ FINAL VERDICT")
    print("-" * 40)

    print("PACKAGE APPROVED")
    print(
        f"'{package_name}' passed static analysis "
        "and Docker sandbox testing."
    )

    print("=" * 60)


def main():

    parser = argparse.ArgumentParser(
        prog="safe-pip",
        description="GhostPkg secure Python package installer"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    install_parser = subparsers.add_parser(
        "install",
        help="Safely check and test a package"
    )

    install_parser.add_argument(
        "package",
        help="Name of the package to check"
    )

    args = parser.parse_args()

    if args.command == "install":
        show_result(args.package)


if __name__ == "__main__":
    main()
