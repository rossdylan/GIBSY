from setuptools import setup
from subprocess import check_call

#There is probably a better way to do this..
check_call(['easy_install', 'https://github.com/rossdylan/python-daemon/zipball/master#egg=python-daemon'])
setup(
        name = "GIBSY",
        description = "Git Blogging System",
        long_description="Lightweight blogging system based around git",
        author = "Ross Delinger",
        author_email = "rossdylan@csh.rit.edu",
        scripts = ['gibsy.py',],
        license = 'MIT',
        dependency_links = ['https://github.com/rossdylan/python-daemon/zipball/master#egg=python-daemon',],
        install_requires = ['fapws3', 'PyRSS2Gen', 'docutils'])


