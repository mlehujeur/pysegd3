import os
import setuptools

setuptools.setup(
    name='pysegd3',
    version="1.0.1",
    license='GPL3',
    author="Maximilien Lehujeur",
    author_email="maximilien.lehujeur@univ-eiffel.fr",
    decription='Standalone package to read/write segd rev3 files in python',
    long_description='Standalone package to read/write segd rev3 files in python',
    long_description_content_type='text/x-rst',
    packages=setuptools.find_packages(),
    install_requires=['numpy', 'pytest', 'matplotlib'],
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
