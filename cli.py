import argparse
import sys

from pypi_check import run_security_check


def show_result(package_name, result):
    verdict = result["verdict"]

    print("=" * 60)
    print("                    GHOSTPKG")
    print("=" * 60)
    print(f"\n📦 Package: {package_name}")

    print("\n🔍 PYPI VERIFICATION")
    print("-" * 40)
    if verdict["exists"] is True:
        print("PyPI:          EXISTS")
    elif verdict["exists"] is False:
        print("PyPI:          NOT FOUND")
    else:
        print("PyPI:          UNKNOWN")

    print(f"Reason:        {verdict['reason']}")

    if verdict["closest_match"]:
        print(f"💡 Similar package: '{verdict['closest_match']}'")

    if verdict["created"]:
        print(f"First published: {verdict['created']}")

    if result["stage"] == "pypi":
        print("\n🚨 SECURITY DECISION")
        print("-" * 40)
        print("🛑 PACKAGE BLOCKED")
        print(f"\nReason: {result['message']}")
        if verdict["closest_match"]:
            print(f"💡 Did you mean '{verdict['closest_match']}'?")
        print("\n🐳 Docker chamber: SKIPPED")
        print("=" * 60)
        return

    sandbox = result["sandbox"]
    print("\n🧪 DETONATION CHAMBER")
    print("-" * 40)
    print("Docker:        ENTERED")
    print(f"Status:        {sandbox['status']}")
    print(f"Exit code:     {sandbox['exit_code']}")

    if not result["success"]:
        print("\n🚨 SECURITY DECISION")
        print("-" * 40)
        print("🛑 PACKAGE BLOCKED")
        print("\nReason: Package failed Docker sandbox testing.")
        print("=" * 60)
        return

    print("\n✅ SECURITY DECISION")
    print("-" * 40)
    print("PACKAGE APPROVED")
    print("\n✓ Package exists on PyPI")
    print("✓ Docker sandbox passed")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(prog="ghostpkg", description="GhostPkg - secure Python package installer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Securely verify and test a Python package")
    install_parser.add_argument("package", help="Python package name")

    args = parser.parse_args()

    if args.command == "install":
        result = run_security_check(args.package)
        show_result(args.package, result)
        return 0 if result["success"] else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
