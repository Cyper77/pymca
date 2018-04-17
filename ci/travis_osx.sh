# Script for travis-CI Mac OS X specific setup.
# source this script with PYTHON_VERSION env variable set

if [ "$TRAVIS_OS_NAME" == "osx" ]; then

    VENV_DIR=./venv


    brew upgrade python@3;
    PYTHON_EXE=`brew list python@3 | grep "bin/python3$" | head -n 1`;
    # Create virtual env
    $PYTHON_EXE -m venv $VENV_DIR
    source $VENV_DIR/bin/activate

    # Alternative python installation using miniconda
    #curl -o miniconda_installer.sh "https://repo.continuum.io/miniconda/Miniconda$PYTHON_VERSION-latest-MacOSX-x86_64.sh"
    #bash miniconda_installer.sh -b -p miniconda
    #export PATH="`pwd`/miniconda/bin":$PATH

fi