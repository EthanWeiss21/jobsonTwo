from setuptools import setup, find_packages

setup(
    name="jobsonTwo",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "pyyaml>=6.0",
        "textblob>=0.17.1",
        "langdetect>=1.0.9",
        "nltk>=3.8.1",
        "pillow>=10.0.0",
    ],
    python_requires=">=3.8",
) 