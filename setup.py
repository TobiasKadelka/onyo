#!/usr/bin/env python3
''' setup file for installation of onyo '''
from setuptools import setup, find_packages

setup(
    name='onyo',
    version='1.0.1',
    description='Textual inventory system backed by git.',
    author='Tobias Kadelka',
    author_email='t.kadelka@fz-juelich.de',
    packages=find_packages(),
    license='ISC',
    install_requires=[
#        'subprocess',
#        'logging',
#        'os',
#        'sys',
#       'argparse'
    ],
    python_requires=">=3.0",
    scripts=[
        'onyo/onyo_mv',
        'onyo/onyo_init',
        'onyo/onyo_new'
    ],
)
