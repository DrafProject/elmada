# How to contribute

To guarantee the further evolution of elmada in the long term, we depend on the support of volunteer developers.

Some of the resources to look at if you're interested in contributing:
* [Join us on Gitter to chat!](https://gitter.im/DrafProject/elmada)

## Licensing

By contributing to elmada, e.g. through opening a pull request or submitting a patch, you represent that your contributions are your own original work and that you have the right to license them, and you agree that your contributions are licensed under the LGPL 3 license.

## Submitting bug reports

[Open an issue on GitHub](https://github.com/DrafProject/elmada/issues/new) to report bugs or other problems.

## Submitting changes

To contribute changes:

1. Fork the project on GitHub
1. Create a feature branch to work on in your fork (``git checkout -b new-fix-or-feature``)
1. Commit your changes to the feature branch after running black to format your code
1. Push the branch to GitHub (``git push origin new-fix-or-feature``)
1. On GitHub, create a new [pull request](https://github.com/DrafProject/elmada/pull/new/master) from the feature branch

### Pull requests

Before submitting a pull request, check whether you have:

* Added or updated documentation for your changes
* Added tests if you implemented new functionality

When opening a pull request, please provide a clear summary of your changes!

### Commit messages

Please try to write clear commit messages. One-line messages are fine for small changes, but bigger changes should look like this:

    A brief summary of the commit

    A paragraph or bullet-point list describing what changed and its impact,
    covering as many lines as needed.

## Testing

We have existing test coverage for the key functionality of elmada.

All tests are in the ``elmada/tests`` directory and use [pytest](https://docs.pytest.org/en/latest/).

Our test coverage is not perfect. An easy way to contribute code is to work on better tests.

## Coding conventions

Start reading our code and you'll get the hang of it.

We mostly follow the official [Style Guide for Python Code (PEP8)](https://www.python.org/dev/peps/pep-0008/).

We have chosen to use the uncompromising code formatter, [`black`](https://github.com/psf/black/).
If run from the root directory of this repo, `pyproject.toml` should ensure the line lengths are restricted to 100.
The philosophy behind using black is to have uniform style throughout the project dictated by code.
Since `black` is designed to minimise diffs, and make patches more human readable, this also makes code reviews more efficient.

## Attribution

The layout and content of this document is based on the contribution guidelines of the projects [OpenGovernment](https://github.com/opengovernment/opengovernment/blob/master/CONTRIBUTING.md) and [Calliope](https://github.com/calliope-project/calliope/blob/master/CONTRIBUTING.md).
