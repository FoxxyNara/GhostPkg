import argparse
import sys

from safe_pip import run_security_check


def show_result(package_name, result):

    verdict = result["verdict"]

    print("=" * 60)
    print("                    GHOSTPKG")
    print("=" * 60)

    print(f"\n📦 Package: {package_name}")

    # ========================================================
    # PYPI VERIFICATION
    # ========================================================

    print("\n🔍 PYPI VERIFICATION")
    print("-" * 40)

    if verdict["exists"] is True:
        print("PyPI:          EXISTS")

    elif verdict["exists"] is False:
        print("PyPI:          NOT FOUND")

    else:
        print("PyPI:          UNKNOWN")

    print(f"Reason:        {verdict['reason']}")

    if verdict.get("closest_match"):
        print(
            f"💡 Similar package: "
            f"'{verdict['closest_match']}'"
        )

    if verdict.get("created"):
        print(
            f"First published: "
            f"{verdict['created']}"
        )

    # ========================================================
    # PYPI BLOCK
    # ========================================================

    if result["stage"] == "pypi":

        print("\n🚨 SECURITY DECISION")
        print("-" * 40)

        print("🛑 PACKAGE BLOCKED")

        print(
            f"\nReason: {result['message']}"
        )

        if verdict.get("closest_match"):
            print(
                f"💡 Did you mean "
                f"'{verdict['closest_match']}'?"
            )

        print(
            "\n🐳 Docker chamber: SKIPPED"
        )

        print("=" * 60)

        return

    # ========================================================
    # DOCKER DETONATION
    # ========================================================

    sandbox = result.get("sandbox")

    print("\n🧪 DETONATION CHAMBER")
    print("-" * 40)

    print("Docker:        ENTERED")

    if sandbox:

        print(
            f"Status:        "
            f"{sandbox['status']}"
        )

        print(
            f"Exit code:     "
            f"{sandbox['exit_code']}"
        )

        if sandbox.get("risk_score") is not None:
            print(
                f"Risk score:    "
                f"{sandbox['risk_score']}/100"
            )

        if sandbox.get("indicators"):

            print("\n⚠️ Indicators:")

            for indicator in sandbox["indicators"]:
                print(
                    f"  • {indicator}"
                )

    # ========================================================
    # DOCKER FAILURE
    # ========================================================

    if not result["success"]:

        print("\n🚨 SECURITY DECISION")
        print("-" * 40)

        print("🛑 PACKAGE BLOCKED")

        print(
            f"\nReason: "
            f"{result['message']}"
        )

        print("=" * 60)

        return

    # ========================================================
    # APPROVED
    # ========================================================

    print("\n✅ SECURITY DECISION")
    print("-" * 40)

    print("PACKAGE APPROVED")

    print("\n✓ Package exists on PyPI")
    print("✓ Docker sandbox passed")

    print("=" * 60)


def main():

    parser = argparse.ArgumentParser(
        prog="ghostpkg",
        description=(
            "GhostPkg - secure Python "
            "package verification"
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    install_parser = subparsers.add_parser(
        "install",
        help="Verify and test a Python package",
    )

    install_parser.add_argument(
        "package",
        help="Python package name",
    )

    args = parser.parse_args()

    if args.command == "install":

        result = run_security_check(
            args.package
        )

        show_result(
            args.package,
            result
        )

        return (
            0
            if result["success"]
            else 1
        )

    return 1


if __name__ == "__main__":
    sys.exit(main())
