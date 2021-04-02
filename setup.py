from setuptools import find_packages, setup


setup(
    name="pykeepass-cache",
    version="2.0.2",
    license="GPL3",
    description="database caching for PyKeePass",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Evan Widloski",
    author_email="evan@evanw.org",
    url="https://github.com/evidlo/pykeepass-cache",
    packages=find_packages(),
    install_requires=[
        "pykeepass",
        "rpyc",
        "python-daemon"
    ],
    include_package_data=True
)
