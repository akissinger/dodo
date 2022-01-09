import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dodo-mail",
    version="0.1",
    author="Aleks Kissinger",
    author_email="aleks0@gmail.com",
    description="A graphical, hackable email client based on notmuch",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/akissinger/dodo",
    project_urls={
        "Bug Tracker": "https://github.com/akissinger/dodo/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    packages=["dodo"],
    package_data={'': ['*.svg']},
    install_requires=["PyQt5>=5.15", "PyQtWebEngine>=5.15", "PyQt5-sip>=5.15"],
    python_requires=">=3.7",
    entry_points={'console_scripts': 'dodo=dodo.app:main'},
)
