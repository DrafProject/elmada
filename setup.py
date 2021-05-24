from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read().strip()

setup(
    name="elmada",
    version="0.0.1",
    author="Markus Fleschutz",
    author_email="mfleschutz@gmail.com",
    description="Electricity market data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mfleschutz/elmada",
    license="LGPLv3",
    packages=find_packages(),
    python_requires=">=3.6",
    install_require=["scipy", "seaborn", "plotly", "entsoe", "requests", "bs4"],
    tests_require=["pathlib", "pytest"],
)
