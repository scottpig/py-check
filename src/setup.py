'''
Created on Jan 13, 2013

@author: Scott Pigman
'''
from distutils.core import setup

setup(
    name='pycheck',
    version='0.1',
    description='Type checking tools for debugging and developing Python',
    packages=['pycheck', 'pycheck.test'],
    classifiers=[
                 'Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: MIT License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Software Development',
                 'Intended Audience :: Developers'
                ],
    long_description=open('README.TXT').read(),
    author='Scott Pigman',
    author_email='scott.pigman@gmail.com',
    
)