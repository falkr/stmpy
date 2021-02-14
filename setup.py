import codecs
import os.path
from distutils.core import setup


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


package_name = "stmpy"

setup(
    name=package_name,
    packages=[package_name],
    version=get_version("{}/__init__.py".format(package_name)),
    description="Support for state machines",
    author="Frank Alexander Kraemer",
    author_email="kraemer.frank@gmail.com",
    license="MIT",
    url="https://github.com/falkr/stmpy",
    download_url="https://github.com/falkr/stmpy/archive/0.2.tar.gz",
    keywords=["state machines", "stm", "automata"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
