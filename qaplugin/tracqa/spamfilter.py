# -*- coding: utf-8 -*-
"""
Spam filter adapter.

(c) 2010
"""

from trac.core import *
from trac.resource import Resource
from trac.util import arity
from trac.util.compat import set
from trac.util.text import to_unicode
from tracspamfilter.api import FilterSystem
from tracqa.api import ITestCaseManipulator
from tracqa.model import TestCase


class QaSpamFilterAdapter(Component):
    """Pass TCs and comments through the spam filter."""

    implements(ITestCaseManipulator)

    # ITestCaseManipulator methods

    def validate_test_case(self, req, postname, version, fields):
        if 'testcase-preview' in req.args:
            return []

        qa_res = Resource('qa', postname, version)
        
        if req.perm(qa_res).has_permission('QA_ADMIN'):
            return []

        if version > 1:
            bp = BlogPost(self.env, postname, version)
            last_post_fields = bp._fetch_fields(version=version-1)
        else:
            last_post_fields = {}

        field_names = set(fields).union(last_post_fields)
        changes = []
        
        for field in field_names:
            old = to_unicode(last_post_fields.get(field, ''))
            new = to_unicode(fields.get(field, ''))
            if new and old != new:
                changes.append((old, new))
        author = fields.get('author', '')
        
        if arity(FilterSystem.test) == 4:
            # 0.11 compatible method signature
            FilterSystem(self.env).test(req, author, changes)
        else:
            # 0.12+ compatible that adds an 'ip' argument
            FilterSystem(self.env).test(req, author, changes, req.remote_addr)
        return []

    def validate_test_case_comment(self, req, postname, fields):
        if 'previewcomment' in req.args:
            return []

        qa_res = Resource('qa', postname)
        
        if req.perm(qa_res).has_permission('QA_ADMIN'):
            return []

        author = fields.get('author', '')
        changes = [(None, fields.get('comment', '')),
                   (None, author)]
        
        if arity(FilterSystem.test) == 4:
            # 0.11 compatible method signature
            FilterSystem(self.env).test(req, author, changes)
        else:
            # 0.12+ compatible that adds an 'ip' argument
            FilterSystem(self.env).test(req, author, changes, req.remote_addr)
        return []
