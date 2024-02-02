import os
import setuptools

with open('README.md', 'r', encoding="utf-8") as fid:
    long_description = fid.read()

setuptools.setup(
    name='pysegd3',
    version="1.0.2",
    license='GPL3',
    author="Maximilien Lehujeur",
    author_email="maximilien.lehujeur@univ-eiffel.fr",
    decription='Standalone package to read/write segd rev3 files in python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    install_requires=[
        'numpy', 'pytest', 'matplotlib', 
        'tempoo>=1.1.0',  # version required for gps 2 utc time conversions
        ], 
    python_requires=">=3.7",  
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        ],
    scripts=[
        os.path.join('pysegd3', 'readsegd3.py'),
        os.path.join('pysegd3', 'readsegd3_as_obspy.py'),
        ],
    )
