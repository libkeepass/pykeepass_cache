from setuptools import find_packages, setup


setup(
    name="pykeepass-remote",
    version="2",
    license="GPL3",
    description="database caching for PyKeePass",
    author="Evan Widloski",
    author_email="evan@evanw.org",
    url="https://github.com/evidlo/pykeepass-remote",
    packages=find_packages(),
    install_requires=[
        "pykeepass",
        "rpyc",
        "python-daemon"
    ],
    include_package_data=True
)
