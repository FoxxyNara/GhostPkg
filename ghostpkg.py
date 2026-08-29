import argparse

from safe_pip import run_security_check


# ============================================================
# GHOSTPKG
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        prog="ghostpkg",
        description="GhostPkg - secure Python package verification"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    # ========================================================
    # INSTALL COMMAND
    # ========================================================

    install_parser = subparsers.add_parser(
        "install",
        help="Verify and test a Python package"
    )

    install_parser.add_argument(
        "package",
        help="Python package name"
    )

    args = parser.parse_args()

    # ========================================================
    # INSTALL
    # ========================================================

    if args.command == "install":

        package_name = args.package

        print("=" * 60)
        print("                    GHOSTPKG")
        print("=" * 60)

        print(
            f"\n📦 Package: {package_name}"
        )

        # ====================================================
        # RUN SECURITY PIPELINE
        # ====================================================

        result = run_security_check(
            package_name
        )

        verdict = result["verdict"]

        # ====================================================
        # PYPI VERIFICATION
        # ====================================================

        print("\n🔍 PYPI VERIFICATION")
        print("-" * 40)

        if verdict["exists"] is True:

            print("PyPI:          EXISTS")

        elif verdict["exists"] is False:

            print("PyPI:          NOT FOUND")

        else:

            print("PyPI:          UNKNOWN")

        print(
            f"Reason:        {verdict['reason']}"
        )

        # ====================================================
        # TOP-100 SUGGESTION
        # ====================================================

        if verdict.get("closest_match"):

            print(
                f"💡 Similar package: "
                f"'{verdict['closest_match']}'"
            )

        # ====================================================
        # FIRST PUBLISHED
        # ====================================================

        if verdict.get("created"):

            print(
                f"First published: "
                f"{verdict['created']}"
            )

        # ====================================================
        # PYPI BLOCK
        # ====================================================

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

            return 1

        # ====================================================
        # DOCKER DETONATION
        # ====================================================

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

        # ====================================================
        # DOCKER FAILURE
        # ====================================================

        if not result["success"]:

            print("\n🚨 SECURITY DECISION")
            print("-" * 40)

            print("🛑 PACKAGE BLOCKED")

            print(
                "\nReason: Package failed "
                "Docker sandbox testing."
            )

            print("=" * 60)

            return 1

        # ====================================================
        # APPROVED
        # ====================================================

        print("\n✅ SECURITY DECISION")
        print("-" * 40)

        print("PACKAGE APPROVED")

        print(
            "\n✓ Package exists on PyPI"
        )

        print(
            "✓ Docker sandbox passed"
        )

        print("=" * 60)

        return 0

    return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )
