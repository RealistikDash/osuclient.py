from setuptools import setup

def parse_requirements() -> list[str]:
    with open("requirements.txt") as f:
        lines = f.readlines()

    return [
        line for line in lines
        if line and not line.startswith("#")
    ]

def read_readme() -> str:
    with open("README.md") as f:
        return f.read()

setup(
    name= "osuserver.py",
    version= "0.1.0",
    description= "A simple library for programmatic interfacing with osu servers. ",
    license= "MIT",
    classifiers= [
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.7",

    install_requires= parse_requirements(),
    package_dir= {"": "osuclient"},

    url= "https://github.com/RealistikDash/osuclient.py",
    project_urls= {
        "GitHub: repo": "https://github.com/RealistikDash/osuclient.py",
        "GitHub: issues": "https://github.com/RealistikDash/osuclient.py/issues"
    },

    long_description_content_type= "text/markdown",
    long_description= read_readme(),
)
