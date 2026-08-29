from setuptools import setup, find_packages

setup(
    name="ghostpkg",
    version="1.0.0",
    description="Zero-Trust AI Dependency Firewall and Slopsquatting Protector",
    author="Sharveel Kiran Awari",
    packages=find_packages(where="."),
    py_modules=["cli", "pypi_check", "sandbox", "static_scan"],
    install_requires=[
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "ghostpkg=cli:main",
        ],
    },
    python_requires=">=3.8",
)