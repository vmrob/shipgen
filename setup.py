try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    description='Procedural ship generator for Space Engineers',
    author='manveti',
    license='MIT License',
    url='https://github.com/manveti/shipgen',
    install_requires=['nose'],
    packages=['shipgen'],
    entry_points={
        'console_scripts': [
            'shipgen = shipgen.Main:main'
        ]
    },
    name='shipgen'
)
