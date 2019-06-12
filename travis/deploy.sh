#!/bin/sh
#
# Deploy mocpy for x86_64 archs with python3
#
# Usage:
#   deploy.sh
#
set -e

### Build the wheels ###
$PIP install cibuildwheel==0.11.1 setuptools-rust
export CIBW_BEFORE_BUILD="pip install setuptools-rust && curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain nightly -y"
export CIBW_ENVIRONMENT='PATH="$HOME/.cargo/bin:$PATH"'
cibuildwheel --output-dir dist
### Upload the wheels to PyPI ###
# If the commit is tagged
if [[ $TRAVIS_TAG ]]; then
    $PIP install twine
    $PYTHON -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*.whl --skip-existing
fi
