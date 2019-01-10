import setuptools
from setuptools.command.test import test
import sys

try:
    from flask_executor import __version__ as version
except ImportError:
    import re
    pattern = re.compile(r"__version__ = '(.*)'")
    with open('flask_executor/__init__.py') as f:
        version = pattern.search(f.read()).group(1)


with open("README.md", "r") as fh:
    long_description = fh.read()


class pytest(test):

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setuptools.setup(
    name='Flask-Executor',
    version=version,
    author='Dave Chevell',
    author_email='chevell@gmail.com',
    description='An easy to use Flask wrapper for concurrent.futures',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/dchevell/flask-executor',
    packages=setuptools.find_packages(exclude=["tests"]),
    keywords=['flask', 'concurrent.futures'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license='MIT',
    install_requires=['Flask'],
    extras_require={
        ':python_version == "2.7"': ['futures>=3.1.1']
    },
    tests_require=['pytest', 'pytest-flask', 'python-coveralls'],
    test_suite='tests',
    cmdclass={
        'test': pytest
    }
)
