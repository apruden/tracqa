# -*- coding: utf-8 -*-
"""
API interfaces.

(c) 2010
"""
from trac.core import Interface

class ITestCaseChangeListener(Interface):
    """Extension point interface for components that should get notified about
    creation, change or deletion of blog posts + adds and deletes of blog comments."""

    def test_case_changed(postname, version):
        """Called when a new blog post 'postname' with 'version' is added .
        version==1 denotes a new post, version>1 is a new version on existing post."""

    def test_case_deleted(postname, version, fields):
        """Called when a test case is deleted:
        version==0 means all versions (or last remaining) version is deleted.
        Any version>0 denotes a specific version only.
        Fields is a dict with the pre-existing values of the blog post.
            If all (or last) the dict will contain the 'current' version contents."""

    def test_case_comment_added(postname, number):
        """Called when test case comment number N on post 'postname' is added."""

    def test_case_comment_deleted(postname, number, fields):
        """Called when blog post comment 'number' is deleted.
        number==0 denotes all comments is deleted and fields will be empty.
            (usually follows a delete of the blog post).
        number>0 denotes a specific comment is deleted, and fields will contain
            the values of the fields as they existed pre-delete."""

class ITestCaseManipulator(Interface):
    """Extension point interface for components that need to manipulate the content
    of blog posts and comments before insertion.
    
    Unlike change listeners, a manipulator can reject changes being committed
    to the database.
    """

    def validate_test_case(req, postname, version, fields):
        """Validate test case fields before they are to be inserted as new version.
        version==1 denotes a new post, version>1 is a new version on existing post.
        Fields is a dict of the fields needed for insert by model.BlogPost.
                
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        post. Therefore, a return value of `[]` means everything is OK."""

    def validate_test_case_comment(req, postname, fields):
        """Validate new test case fields before comment gets added to 'postname'
        Fields is a dict of the fields needed for insert by model.BlogComment.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        comment. Therefore, a return value of `[]` means everything is OK."""
