import argparse
from pypi_check import check_package


def show_result(package_name):
    verdict = check_package(package_name)

    if verdict["status"] == "blocked":
        print(f"[BLOCKED] '{package_name}' does not appear to be a real PyPI package.")
    elif verdict["status"] == "suspicious":
        print(f"[WARNING] '{package_name}' is suspiciously close to '{verdict['closest_match']}'. Did you mean that?")
    else:
        print(f"[OK] '{package_name}' looks safe. First published: {verdict['created']}.")


def main():
    parser = argparse.ArgumentParser(prog="safe-pip")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Safely check and install a package")
    install_parser.add_argument("package", help="Name of the package to install")

    args = parser.parse_args()

    if args.command == "install":
        show_result(args.package)


if __name__ == "__main__":
    main()