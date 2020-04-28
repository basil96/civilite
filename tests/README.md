# Running Tests

## Install requirements-test.txt

1. Activate the virtual environment for this project.

1. Run **pip install -r requirements-test.txt** to install the dependencies for the tests.

## Add civilite to sys.path

There is no proper package set up yet in the project.  Until then, the simplest way to have the package available to a top-level script is to add the fully qualified path to the **src** directory to a .pth file in the virtual environment's **Lib/site-packages** directory.  Any file name will do as long as its extension is **.pth**.

## Run pytest

1. Change into the **tests** directory and type **pytest** on the command line to execute the tests. The unit tests have been structured and named according to pytest's discovery rules so that pytest will discover them automatically.
