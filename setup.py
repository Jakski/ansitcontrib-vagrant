import re
from setuptools import setup, find_packages


def get_latest_version(changelog):
    '''Retrieve latest version of package from changelog file.'''
    # Match strings like "## [1.2.3] - 2017-02-02"
    regex = r'^##\s*\[(\d+.\d+.\d+)\]\s*-\s*\d{4}-\d{2}-\d{2}$'
    with open(changelog, "r") as changelog:
        content = changelog.read()
    return re.search(regex, content, re.MULTILINE).group(1)

setup(
    name='ansitcontrib-vagrant',
    url='https://github.com/Jakski/ansitcontrib-vagrant',
    author='Jakub Pieńkowski',
    author_email='jakski@sealcode.org',
    license='MIT',
    description='Vagrant provider for Ansit',
    version=get_latest_version('CHANGELOG'),
    packages=['ansitcontrib.vagrant'],
    platforms='linux',
    install_requires=[
        'paramiko'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License'
    ]
)
