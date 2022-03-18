from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='airway_gui',
    version='0.1.0',
    description='The AIrway GUI Python package',
    url='https://github.com/rgroh1996/AIrway_GUI',
    author='René Groh',
    author_email='rene.groh@fau.de',
    license='GPLv3',
    packages=find_packages(),
    install_requires=[
        "pyqtgraph>=0.10.0",
        "numpy",
        "flammkuchen",
        "pyqt5",
        "scipy",
        "simpleaudio",
        "pandas"
    ],

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="annotation, labelling",
    project_urls={
        "Source": "https://github.com/rgroh1996/AIrway_GUI",
        "Tracker": "https://github.com/rgroh1996/AIrway_GUI/issues",
    },
    entry_points={
        'console_scripts': [
            'airway-gui = AIrway_GUI.main:main'
        ]
    },
    include_package_data=True,
)