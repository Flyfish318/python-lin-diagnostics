#!/usr/bin/env python

import setuptools

with open("README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(name='lindiagnostics',
      version='0.0.1',
      description='A Diagnostic over LIN (LIN-TP) client.',
      long_description=long_description,
      author='Jacob Schaer',
      url='https://github.com/jacobschaer/python-lin-diagnostics',
      packages=setuptools.find_packages(),
      keywords = ['uds', '14229', 'iso-14229', 'diagnostic', 'automotive', 'lin', 'lintp', '17987', 'iso-17987'], 
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
      ],
      python_requires='>=3.6'
     )
