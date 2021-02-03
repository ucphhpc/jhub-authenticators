import os
from setuptools import setup, find_packages

here = os.path.dirname(__file__)


def read(path):
    with open(path, "r") as _file:
        return _file.read()


def read_req(name):
    path = os.path.join(here, name)
    return [req.strip() for req in read(path).splitlines() if req.strip()]


version_ns = {}
with open(os.path.join(here, "version.py")) as f:
    exec(f.read(), {}, version_ns)

long_description = open("README.rst").read()

setup(
    name="jhub-authenticators",
    version=version_ns["__version__"],
    description="A collection of HTTP(s) JupyterHub Header Authenticators,"
    "includes Header, Remote-User and Dummy",
    long_description=long_description,
    author="Rasmus Munk",
    author_email="munk1@live.dk",
    license="GPLv3",
    keywords=["Interactive", "Interpreter", "Shell", "Web"],
    url="https://github.com/rasmunk/jhub-authenticators",
    packages=find_packages(),
    install_requires=read_req("requirements.txt"),
    extras_require={
        "test": read_req("tests/requirements.txt"),
        "dev": read_req("requirements-dev.txt"),
    },
    project_urls={"Source Code": "https://github.com/rasmunk/jhub-authenticators"},
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    platforms="Linux, Mac OSX",
)
