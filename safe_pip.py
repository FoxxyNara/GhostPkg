from pypi import check_pypi_exists
from sandbox import test_install_in_sandbox


def run_security_check(package_name: str) -> dict:
    """GhostPkg security pipeline execution."""
    verdict = check_pypi_exists(package_name)

    if verdict["status"] == "unknown":
        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": verdict,
            "sandbox": None,
            "message": (
                "Unable to verify package existence because the PyPI lookup failed."
            ),
        }

    if verdict["exists"] is False:
        return {
            "success": False,
            "stage": "pypi",
            "package": package_name,
            "verdict": verdict,
            "sandbox": None,
            "message": "Package does not exist on PyPI.",
        }

    sandbox_result = test_install_in_sandbox(package_name)

    if not sandbox_result["success"]:
        return {
            "success": False,
            "stage": "sandbox",
            "package": package_name,
            "verdict": verdict,
            "sandbox": sandbox_result,
            "message": "Package failed Docker sandbox testing.",
        }

    return {
        "success": True,
        "stage": "complete",
        "package": package_name,
        "verdict": verdict,
        "sandbox": sandbox_result,
        "message": "Package exists on PyPI and passed Docker sandbox testing.",
    }


if __name__ == "__main__":
    packages = [
        "requests",
        "numpy",
        "this-package-definitely-does-not-exist-12345",
    ]

    for package in packages:
        print("\n" + "=" * 60)
        print(f"Testing: {package}")
        result = run_security_check(package)
        print(result)
