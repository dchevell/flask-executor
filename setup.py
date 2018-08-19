import setuptools

from flask_executor import __version__ as version

with open("README.md", "r") as fh:
    long_description=fh.read()


setuptools.setup(
    name='Flask-Executor',
    version=version,
    author='Dave Chevell',
    author_email='chevell@gmail.com',
    description='A simple Flask wrapper for concurrent.futures',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/dchevell/flask-executor',
    packages=setuptools.find_packages(),
    keywords=['flask', 'concurrent.futures'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license='MIT',
    install_requires=['Flask'],
    python_requires='>=3.3.0'
)
