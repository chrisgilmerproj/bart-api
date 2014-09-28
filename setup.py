from setuptools import setup, find_packages

setup(
    name='bart',
    version=__import__('bart').__version__,
    author='Chris Gilmer',
    author_email='chris.gilmer@gmail.com',
    maintainer='Chris Gilmer',
    maintainer_email='chris.gilmer@gmail.com',
    description='Python implementation of the BART API',
    url='https://www.github.com/chrisgilmerproj/bart-api',
    packages=find_packages(exclude=["*.tests",
                                    "*.tests.*",
                                    "tests.*",
                                    "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=['requests>=2.4.1',
                      'xmltodict>=0.9.0',
                      ],
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
    ),
)
