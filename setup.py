from setuptools import find_packages, setup

setup(
    name="momo_analytics",
    version="0.2.0",
    description="A small library for tracking and analyzing mobile money transactions.",
    packages=find_packages(exclude=["tests"]),
    install_requires=["pandas>=1.5"],
    extras_require={"dev": ["pytest>=7.0"]},
    python_requires=">=3.9",
)
