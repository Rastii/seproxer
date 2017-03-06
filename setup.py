import setuptools
import codecs
from os import path


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs.open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setuptools.setup(
    name="seproxer",
    version="0.0.1",
    description="Tests specified URLs for common errors, not writing any custom unit tests, by"
                "using selenium_extensions and mitmproxy",
    long_description=long_description,
    author="Luke Hritsko",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Environment :: Web Environment",
        "License :: OSI Approved :: MIT License",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Testing :: Traffic Generation",
    ],
    keywords="browser testing selenium mitmproxy",
    packages=setuptools.find_packages(exclude=["docs"]),
    entry_points={
        "console_scripts": [
            'seproxer=runner:main',
        ]
    },
    install_requires=[
        "selenium_extensions>=3.0.2",
        "mitmproxy>=2.0.0",
        "beautifulsoup4>=4.5.3",
    ],
    extras_require={
        "lint": [
            "mypy>=0.471",
            "flake8>=3.3.0",
        ]
    }
)
