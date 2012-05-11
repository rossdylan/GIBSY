try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_package

f = open('README.md')
long_description = f.read().strip()
f.close()

from subprocess import check_call

#There is probably a better way to do this..
check_call(['easy_install', 'https://github.com/rossdylan/python-daemon/zipball/master#egg=python-daemon'])
setup(
    name='gibsy',
    version='2.0.0',
    description="Git Blogging SYstem",
    long_description=long_description,
    author='Ross Delinger',
    author_email='rossdylan@csh.rit.edu',
    url='http://github.com/rossdylan/GIBSY',
    license='MIT',
    classifiers=[
        "License :: OSI Approved :: MIT",
        "Programming Lnaguage :: Python :: 2"
    ],
    install_requires=[
        'fapws3',
        'PyRSS2Gen',
        'pygments',
        'docutils>=0.9'
        ],
    packages=['gibsy'],
    include_package_data=True,
    zip_safe=False,
    entry_points="""
    [console_scripts]
    gibsy = gibsy:gibsy_main
    """
)
