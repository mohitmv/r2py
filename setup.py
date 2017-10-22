# This is purely the result of trial and error.

import sys
import codecs

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
	# `$ python setup.py test' simply installs minimal requirements
	# and runs the tests with no fancy stuff like parallel execution.
	def finalize_options(self):
		TestCommand.finalize_options(self)
		self.test_args = [
			'--doctest-modules', '--verbose',
			'./r2py', './tests'
		]
		self.test_suite = True

	def run_tests(self):
		import pytest
		sys.exit(pytest.main(self.test_args))


tests_require = [
	'pytest',
	'mock',
]


dependency_links = [
	"https://github.com/mohitmv/msl/archive/v1.0.0.tar.gz"
]


# Conditional dependencies:

# sdist
if 'bdist_wheel' not in sys.argv:
	try:
		# noinspection PyUnresolvedReferences
		import argparse
	except ImportError:
		install_requires.append('argparse>=1.2.1')

	if 'win32' in str(sys.platform).lower():
		# Terminal colors for Windows
		install_requires.append('colorama>=0.2.4')


# bdist_wheel
extras_require = {
	# http://wheel.readthedocs.io/en/latest/#defining-conditional-dependencies
	':python_version == "2.6"'
	' or python_version == "2.7"'
	' or python_version == "2.5" ': ['argparse>=1.2.1'],
	':sys_platform == "win32"': ['colorama>=0.2.4'],
}


long_description = "Convert R code into Python";


setup(
	name='r2py',
	version="1.0.0",
	description="r2py",
	long_description=long_description,
	url='http://stillhungry.in/',
	download_url='https://github.com/mohitmv/r2py',
	author="Mohit Saini",
	author_email='mohitsaini1196@gmail.com',
	license="",
	packages=find_packages(),
	entry_points={
		# 'console_scripts': [
		# 	'http = r2py.__main__:main',
		# ],
	},
	extras_require=extras_require,
	dependency_links = dependency_links, 
	tests_require=tests_require,
	cmdclass={'test': PyTest},
	classifiers=[
		'First Version Released - Production/Stable',
	],
)


