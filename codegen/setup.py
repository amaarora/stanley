"""Setup configuration for Stanley Codegen."""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="stanley-codegen",
    version="0.1.0",
    author="Stanley AI",
    description="Generate Stanley agents from simple tool specifications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stanley-ai/stanley-codegen",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0",
        "pydantic>=2.0",
        "pyyaml>=6.0",
        "rich>=13.0",
        "jinja2>=3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "stanley-codegen=stanley_codegen.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
