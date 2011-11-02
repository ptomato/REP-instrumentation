#!/usr/bin/env python

from distutils.core import setup

setup(name='REP-instrumentation',
    version='0',
    description='Python interfaces to lab instruments',
    author='P. F. Chimento',
    author_email='philip.chimento@gmail.com',
    url='https://github.com/ptomato/REP-instrumentation',
    license='gpl3',
    requires=['pyvisa'],
    py_modules=['Camera', 'ApogeeCam', 'Webcam', 'DirectShow', 'esp300'])