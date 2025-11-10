from setuptools import setup, find_packages

setup(
    name="polyparse",
    version="0.1.0",
    description="CLI tool to scrape Polymarket event data using Selenium",
    author="",
    packages=find_packages(),
    install_requires=[
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.0",
        "click>=8.1.0",
        "python-dateutil>=2.8.2",
    ],
    entry_points={
        "console_scripts": [
            "polyparse=polyparse.cli:main",
        ],
    },
    python_requires=">=3.8",
)


