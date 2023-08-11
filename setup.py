from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as f:
    required = f.read().splitlines()

setup(
    name="home-assistant-findmy",
    version="1.0.0",
    author="muehlt",
    author_email="thomas@savory.at",
    description="A python script that reads local FindMy cache files to broadcast device locations (including those of AirTags, AirPods, Apple Watches, iPhones) to Home Assistant via MQTT.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/muehlt/home-assistant-findmy",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    entry_points={
        'console_scripts': [
            'findmy = findmy:main',
        ],
    },
    install_requires=required,
    python_requires='>=3.6',
)
