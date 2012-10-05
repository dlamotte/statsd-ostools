#!/usr/bin/env python

from setuptools import setup, find_packages

install_requires = [
    'setproctitle==1.1.6',
    'statsd==1.0.0',
]

setup(
    name='statsd-ostools',
    version='0.2',
    author='Dan LaMotte',
    author_email='lamotte85@gmail.com',
    url='https://github.com/dlamotte/statsd-ostools',
    description='Tools for sending OS performance data to statsd',
    long_description=open('README.md').read(),
    packages=find_packages('.'),
    zip_safe=False,
    install_requires=install_requires,
    #tests_require=[],
    license='',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'statsd-ostools = statsd_ostools.cmd:main'
        ],
    },
    classifiers=[],
)
