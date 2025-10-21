from pathlib import Path
from setuptools import setup, find_packages

this_dir = Path(__file__).parent

setup(
    name="photo-cleaner",
    version="1.0.0",
    description="Strip metadata and hidden data from image files",
    long_description=(this_dir / "README.md").read_text(),
    long_description_content_type="text/markdown",
    author="<YOUR NAME>",
    url="https://github.com/<YOUR_USER>/photo-cleaner",
    py_modules=["cleanphotos"],
    entry_points={"console_scripts": ["cleanphotos=cleanphotos:main"]},
    python_requires=">=3.8",
    install_requires=[
        "pillow>=10.0.0",
        "tqdm>=4.65.0",
    ],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
)