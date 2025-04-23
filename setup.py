from setuptools import setup, find_packages

setup(
    name="sharingan",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.26.0",
        "fake-useragent>=0.1.11",
    ],
    python_requires=">=3.6",
)