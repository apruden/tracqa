# -*- coding: utf-8 -*-
"""
Trac plugin providing QA features.
(c) 20010
"""

from setuptools import setup

setup(name='TracQaPlugin',
      version='0.1.0',
      packages=['tracqa'],
      author='Alex Prudencio',
      author_email='alex.prudencio@gmail.com',
      keywords='trac qa',
      description='QA features.',
      url='http://trac-hacks.org/wiki/EnableQaPlugin',
      license='BSD',
      zip_safe = False,
      extras_require={
            'tags': 'TracTags>=0.6',
            'spamfilter': 'TracSpamFilter>=0.2'},
      entry_points={'trac.plugins': [
            'tracqa.admin = tracqa.admin',
            'tracqa.core = tracqa.core',
            'tracqa.db = tracqa.db',
            'tracqa.macros = tracqa.macros',
            'tracqa.spamfilter = tracqa.spamfilter[spamfilter]',
            'tracqa.tags = tracqa.tags[tags]',
            'tracqa.web_ui = tracqa.web_ui']},
      package_data={'tracqa' : ['htdocs/*.png',
                                'htdocs/css/*.css',
                                'htdocs/js/*.js',
                                'templates/*.html',
                                'templates/*.rss', ]},
      exclude_package_data={'': ['tests/*']},
      test_suite = 'tracqa.tests.test_suite',
      tests_require = [],
      install_requires = [])
