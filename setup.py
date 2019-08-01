from setuptools import find_packages, setup


setup(
    name="pykeepass-remote",
    version="1",
    license="GPL3",
    description="Python library to interact with keepass databases "
                "(supports KDBX3 and KDBX4)",
    # long_description=open("README.rst").read(),
    author="Evan Widloski",
    author_email="evan@evanw.org",
    url="https://github.com/evidlo/pykeepass-remote",
    packages=find_packages(),
    install_requires=[
        "pykeepass",
        "Pyro5"
    ],
    include_package_data=True
)
