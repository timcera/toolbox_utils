import subprocess
import sys

from setuptools import setup

pkg_name = "toolbox_utils"

version = open("VERSION").readline().strip()

if sys.argv[-1] == "publish":
    subprocess.check_output("cleanpy .", shell=False)
    subprocess.check_output("python setup.py sdist", shell=False)
    subprocess.check_output(
        f"twine upload dist/{pkg_name}-{version}.tar.gz",
        shell=False,
    )
    sys.exit()

setup()
