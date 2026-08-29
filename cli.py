import argparse
from safe_pip import run_security_check


def show_result(package_name, result):
    verdict = result["verdict"]

    print("=" * 60)
    print("                    GHOSTPKG")
    print("=" * 60)
    print(f"\n📦 Package: {package_name}")

    print("\n🔍 PACKAGE VERIFICATION")
    print("-" * 40)
    if verdict["exists"] is True:
        print("PyPI:          EXISTS")
        if verdict["closest_match"]:
            print(f"Similarity:    close to '{verdict['closest_match']}'")
        if verdict["created"]:
            print(f"First published: {verdict['created']}")
    elif verdict["exists"] is False:
        print("PyPI:          NOT FOUND")
        if verdict["closest_match"]:
            print(f"💡 Did you mean '{verdict['closest_match']}'?")
    else:
        print("PyPI:          UNKNOWN (lookup failed)")

    if result["stage"] == "pypi":
        print("\n🚨 SECURITY DECISION")
        print("-" * 40)
        print("🛑 BLOCKED")
        print(f"Reason: {verdict['reason']}")
        print("Docker chamber: SKIPPED")
        print("=" * 60)
        return

    sandbox = result["sandbox"]
    print("\n🧪 DETONATION CHAMBER")
    print("-" * 40)
    print(f"Status:    {sandbox['status']}")
    print(f"Exit code: {sandbox['exit_code']}")

    print("\n" + ("✅ SECURITY DECISION" if result["success"] else "🚨 SECURITY DECISION"))
    print("-" * 40)
    if result["success"]:
        print("PACKAGE APPROVED")
        print("PyPI verification: PASSED")
        print("Docker sandbox:    PASSED")
    else:
        print("🛑 BLOCKED")
        print("Reason: Package failed Docker sandbox testing.")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(prog="safe-pip", description="Secure Python package installer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Securely verify and test a Python package")
    install_parser.add_argument("package", help="Python package name")

    args = parser.parse_args()

    if args.command == "install":
        result = run_security_check(args.package)
        show_result(args.package, result)
        return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
