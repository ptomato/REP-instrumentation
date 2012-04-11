#!/usr/bin/env python

from distutils.core import setup

setup(name='REP-instrumentation',
    version='0',
    description='Python interfaces to lab instruments',
    author='P. F. Chimento',
    author_email='philip.chimento@gmail.com',
    url='https://github.com/ptomato/REP-instrumentation',
    license='gpl3',
    requires=[
        'pyvisa',
        'VideoCapture (>= 0.9.5)'
    ],
    packages=[
        'rep',
        'rep.generic',
        'rep.apogee',
        'rep.newport',
        'rep.ocean_optics',
        #'rep.spectra_physics'
    ])