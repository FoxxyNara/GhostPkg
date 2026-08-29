import argparse

from safe_pip import run_security_check


# ============================================================
# GHOSTPKG
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        prog="ghostpkg",
        description=(
            "GhostPkg - secure Python package installer"
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    # --------------------------------------------------------
    # INSTALL COMMAND
    # --------------------------------------------------------

    install_parser = subparsers.add_parser(
        "install",
        help="Securely verify and test a Python package"
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

        result = run_security_check(
            args.package
        )

        print("=" * 60)
        print("                    GHOSTPKG")
        print("=" * 60)

        print(
            f"\n📦 Package: {args.package}"
        )

        # ----------------------------------------------------
        # PYPI RESULT
        # ----------------------------------------------------

        verdict = result["verdict"]

        print("\n🔍 PACKAGE VERIFICATION")
        print("-" * 40)

        if verdict["exists"] is True:

            print("PyPI:          EXISTS")

            if verdict.get("closest_match"):

                print(
                    f"Similarity:    "
                    f"'{verdict['closest_match']}'"
                )

        elif verdict["exists"] is False:

            print("PyPI:          NOT FOUND")

        else:

            print("PyPI:          UNKNOWN")

        # ----------------------------------------------------
        # PYPI BLOCK
        # ----------------------------------------------------

        if result["stage"] == "pypi":

            print("\n🚨 SECURITY DECISION")
            print("-" * 40)

            print("🛑 PACKAGE BLOCKED")

            print(
                f"\nReason: "
                f"{verdict['reason']}"
            )

            if verdict.get("closest_match"):

                print(
                    f"💡 Suggested package: "
                    f"'{verdict['closest_match']}'"
                )

            print(
                "\n🐳 Docker chamber: SKIPPED"
            )

            print("=" * 60)

            return 1

        # ----------------------------------------------------
        # DOCKER RESULT
        # ----------------------------------------------------

        sandbox = result.get("sandbox")

        print("\n🧪 DETONATION CHAMBER")
        print("-" * 40)

        print(
            "Docker:        ENTERED"
        )

        print(
            f"Status:        "
            f"{sandbox['status']}"
        )

        print(
            f"Exit code:     "
            f"{sandbox['exit_code']}"
        )

        # ----------------------------------------------------
        # DOCKER BLOCK
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # APPROVED
        # ----------------------------------------------------

        print("\n✅ SECURITY DECISION")
        print("-" * 40)

        print("PACKAGE APPROVED")

        print(
            "\nPyPI verification: PASSED"
        )

        print(
            "Docker sandbox:    PASSED"
        )

        print("=" * 60)

        return 0

    return 1


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
