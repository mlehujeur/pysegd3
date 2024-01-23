import os
import setuptools

setuptools.setup(
    name='pysegd3',
    version="1.0.0",
    license='GPL3',
    author="Maximilien Lehujeur",
    author_email="maximilien.lehujeur@univ-eiffel.fr",
    decription='Standalone package to read/write segd rev3 files in python',
    packages=setuptools.find_packages(),
    install_requires=['numpy', 'pytest', 'matplotlib'],
    python_requires=">=3.2",  # because of datetime.timezone
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        ],
    scripts=[
        os.path.join('pysegd3', 'readsegd30.py'),
        ],
    )
