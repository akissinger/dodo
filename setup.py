import setuptools

# read description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# linux desktop entry and icons
pngs = [(f'share/icons/hicolor/{res}x{res}/apps', [f'share/icons/hicolor/{res}x{res}/apps/dodo.png'])
        for res in [16, 32, 64, 128, 256, 512, 1024]]

data_files = [
        ('share/applications', ['share/applications/dodo.desktop']),
        ('share/icons/hicolor/scalable/apps', ['share/icons/hicolor/scalable/apps/dodo.svg']),
        ] + pngs

setuptools.setup(
    name="dodo-mail",
    version="0.2",
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
    data_files=data_files,
    install_requires=["PyQt6>=6.2", "PyQt6-WebEngine>=6.2", "bleach>=5.0"],
    python_requires=">=3.7",
    entry_points={'console_scripts': 'dodo=dodo.app:main'},
)
