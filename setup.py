#!/usr/bin/env python

from distutils.core import setup

setup(name='REP-instrumentation',
    version='0.20120411',
    description='Python interfaces to lab instruments',
    author='Philip Chimento',
    author_email='philip.chimento@gmail.com',
    url='http://ptomato.github.com/REP-instrumentation',
    license='gpl3',
    requires=[
        'pyvisa (< 1.5)',
        'VideoCapture (>= 0.9.5)'
    ],
    packages=[
        'rep',
        'rep.generic',
        'rep.apogee',
        'rep.newport',
        'rep.ocean_optics',
        'rep.thorlabs',
        'rep.hp',
        #'rep.spectra_physics'
    ])
