#!/usr/bin/env python

from setuptools import setup
import sendKindle

setup(name='sendKindle',
      version=sendKindle._version,
      py_modules=['sendKindle'],
      entry_points = {
        'console_scripts': ['sendKindle = sendKindle:main'],
      },
      author='Kamil Paral',
      author_email='kamil.paral@gmail.com',
      description='CLI tool for sending files via email to your Kindle device',
      long_description='Configure your email and then send any files provided as program arguments as email attachments to your Kindle device.',
      keywords='commandline Kindle email',
      license='GNU Affero GPL v3',
      url='https://github.com/kparal/sendKindle',
      download_url='https://github.com/kparal/sendKindle/archives/master',
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Topic :: Communications :: Email',
        'Topic :: Utilities',
      ])
