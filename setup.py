from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='wikiclient',
    version='0.0.1',
    install_requires=['cchardet',
                      'aiodns',
                      'requests',
                      'aiohttp',
                      'aioredis'
                      ],
    include_package_data=True,
    packages=find_packages(),
    long_description=open(join(dirname(__file__), 'README.md')).read(),
    url='https://github.com/armymaksim/ArticulMedia',
    author='army.maksim',
    author_email='army.maksim@gmail.com',
    description='Wiki client',
    entry_points={
       'console_scripts':
           ['wikiclient = wikiclient.server:run']
       },
)