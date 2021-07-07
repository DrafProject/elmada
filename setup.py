from pathlib import Path

from setuptools import find_packages, setup

exec(Path("elmada/_version.py").read_text().strip())  # Set the __version__ variable

long_description = Path("README.md").read_text().strip()


# As proposed by Han Xiao in https://hanxiao.io/2019/11/07/A-Better-Practice-for-Managing-extras-require-Dependencies-in-Python
def get_extra_requires(path, add_all=True):
    """Parse extra-requirements.txt for a {feature: requirements} map."""
    import re
    from collections import defaultdict

    with open(path) as fp:
        extra_deps = defaultdict(set)
        for k in fp:
            if k.strip() and not k.startswith("#"):
                tags = set()
                if ":" in k:
                    k, v = k.split(":")
                    tags.update(vv.strip() for vv in v.split(","))
                tags.add(re.split("[<=>]", k)[0])
                for t in tags:
                    extra_deps[t].add(k)

        # add tag `all` at the end
        if add_all:
            extra_deps["all"] = {vv for v in extra_deps.values() for vv in v}

    return extra_deps


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
        "entsoe-py==0.2",
        "fastparquet",
        "ipython",
        "lxml",
        "numpy",
        "pandas",
        "pip",
        "pyarrow",
        "pytables",
        "python-snappy",
        "quandl",
        "requests",
        "scipy",
        "xlrd",
    ],
    extras_require=get_extra_requires("extra-requirements.txt"),
    include_package_data=True,
    package_data={"elmada": ["*.parquet", "*.csv", "*.txt", "*xls"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords=["energy market data", "energy systems", "carbon emission factors", "demand response"],
)
