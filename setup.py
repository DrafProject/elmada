from pathlib import Path

from setuptools import find_packages, setup

exec(Path("elmada/_version.py").read_text().strip())  # Set the __version__ variable

long_description = Path("README.md").read_text().strip()

setup(
    name="elmada",
    version=__version__,
    author="Markus Fleschutz",
    author_email="mfleschutz@gmail.com",
    description="Electricity market data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DrafProject/elmada",
    license="LGPLv3",
    packages=find_packages(exclude=["doc", "tests"]),
    python_requires=">=3.7",
    install_requires=[
        "appdirs",
        "bs4",
        "entsoe-py==0.2.10",
        "ipython",
        "lxml",
        "matplotlib",
        "numpy",
        "pandas",
        "pyarrow",
        "quandl",
        "requests",
        "scipy",
        "xlrd",
    ],
    extras_require={
        "dev": ["plotly", "pytest", "pytest-cov", "pytest-mock", "pytest-responsemock", "mypy"]
    },
    include_package_data=True,
    package_data={"elmada": ["*.parquet", "*.csv", "*.txt", "*xls"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=["energy market data", "energy systems", "carbon emission factors", "demand response"],
)
