from setuptools import setup

setup(
        name = "GIBSY",
        description = "Git Blogging System",
        long_description="Lightweight blogging system based around git",
        author = "Ross Delinger",
        author_email = "rossdylan@csh.rit.edu",
        scripts = ['gibsy.py',],
        license = 'MIT',
        dependency_links = ['https://github.com/rossdylan/python-daemon/tarball/master#egg=python-daemon-git',],
        install_requires = ['fapws3', 'PyRSS2Gen'])


