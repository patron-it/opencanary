from setuptools import setup, find_packages

import sys
import os

requirements = [
    'Twisted==18.7.0',
    'pyasn1==0.4.4',
    'cryptography==2.3.0',
    'simplejson==3.16.0',
    'zope.interface==4.5.0',
    'PyPDF2==1.26.0',
    'fpdf==1.7.2',
    'passlib==1.7.1',
    'Jinja2==2.10.0',
    'ntlmlib==0.72',
    'python-dateutil',
    'click==6.7',
    'six',
    'daemonocle',
]


extras = {
    'rdp': [
        'rdpy',
    ],
    'snmp': [
        'scapy',
        'pcapy',  # undeclared dependency of scapy
    ],
    'DShield': [
        'requests'
    ],
    ':python_version < "3"': [
        'wsgiref==0.1.2',
    ],
}


setup(
    name='patron-it-opencanary',
    use_scm_version=True,
    url='http://www.thinkst.com/',
    author='Thinkst Applied Research',
    author_email='info@thinkst.com',
    description='OpenCanary daemon',
    long_description='A low interaction honeypot intended to be run on internal networks.',
    install_requires=requirements,
    extras_require=extras,
    setup_requires=[
        'setuptools_scm'
    ],
    license='BSD',
    packages=find_packages(exclude='test'),
    entry_points={
        'console_scripts': [
            'opencanaryd = opencanary.cli:main',
        ],
    },
    platforms='any',
    include_package_data=True
)
