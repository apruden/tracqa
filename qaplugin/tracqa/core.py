# -*- coding: utf-8 -*-
"""
TracQa module with core components and functionality
shared across the various access interfaces and modules:
 * Permissions
 * Settings

(c) 2010
"""
import pdb
from time import strftime
from genshi.builder import tag
from trac.attachment import ILegacyAttachmentPolicyDelegate
from trac.core import *
from trac.config import Option
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.resource import IResourceManager
from trac.util.compat import sorted, set
from trac.util.text import unicode_unquote
from trac.util.datefmt import to_datetime, utc
from trac.wiki.api import IWikiSyntaxProvider
from api import ITestCaseChangeListener, ITestCaseManipulator
from model import TestCase, get_testcases_resources
from util import parse_period

class QaCore(Component):
    """ Module implementing features that are common and shared
    between the various parts of the plugin. """

    # Extensions
    listeners = ExtensionPoint(ITestCaseChangeListener)
    manipulators = ExtensionPoint(ITestCaseManipulator)
    implements(IPermissionRequestor, IWikiSyntaxProvider, IResourceManager,
            ILegacyAttachmentPolicyDelegate)

    # Options
    Option('qa', 'default_testcase_name', '',
        """Set the default testcase name""")

    # Constants
    reserved_names = ['create', 'view', 'edit', 'delete',
                    'archive', 'category', 'author']

    def __init__(self):
        self.env.systeminfo.append(('Qa', __import__('tracqa', ['__version__']).__version__))

    # IPermissionRequestor method
    def get_permission_actions(self):
        """ Permissions supported by the plugin.
        Commenting needs special enabling if wanted as it is only enabled
        if user is ADMIN or if specifically given QA_COMMENT permission.
        Apart from that, the permisions follow regular practice of builing
        on top of each other. """
        
        return ['QA_VIEW',
                ('QA_COMMENT', ['QA_VIEW']),
                ('QA_CREATE', ['QA_VIEW']),
                ('QA_MODIFY', ['QA_CREATE']),
                ('QA_ADMIN', ['QA_MODIFY', 'QA_COMMENT'])]

    # ILegacyAttachmentPolicyDelegate methods
    def check_attachment_permission(self, action, username, resource, perm):
        """ Respond to the various actions into the legacy attachment
        permissions used by the Attachment module. """
        if resource.parent.realm == 'qa':
            if action == 'ATTACHMENT_VIEW':
                return 'QA_VIEW' in perm(resource.parent)
            if action in ['ATTACHMENT_CREATE', 'ATTACHMENT_DELETE']:
                if 'QA_MODIFY' in perm(resource.parent):
                    return True
                else:
                    return False

    # IResourceManager methods
    def get_resource_realms(self):
        yield 'qa'

    def get_resource_url(self, resource, href, **kwargs):
        return href.qa(resource.id,
                resource.version and 'version=%d' % (resource.version) or None)
        
    def get_resource_description(self, resource, format = None, context = None,
                                 **kwargs):
        # TODO: define resources description
        if context:
            return tag.a('QA: ' + 'Test case', href=context.href.qa(resource.id))
        else:
            return 'QA: ' + 'Test case'

    def resource_exists(self, resource):
        # TODO: implement
        return True

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        return []
    
    def get_link_resolvers(self):
        yield ('qa', self._testcaselink_formatter)
    
    def _testcaselink_formatter(self, formatter, ns, content, label):
        content = (content.startswith('/') and content[1:]) or content
        path_parts = [part for part in content.split('/') if part != '']
        
        if not content:
            return tag.a(label, href=formatter.href.qa(content))
        if len(path_parts) == 2 and path_parts[0].isdigit() \
                                and path_parts[1].isdigit():
            # Requesting a period listing
            return tag.a(label, href=formatter.href.qa(content))
        elif len(path_parts) and path_parts[0] in self.reserved_names:
            # Requesting a specific path to command or listing
            return tag.a(label, href=formatter.href.qa(content))
        else:
            # Assume it is a regular post, and pass to 'view'
            # Split for comment linking (the_post#comment-1, or #comment-1)
            segments = content.split('#')
            if len(segments) == 2:
                url, anchor = segments
            else:
                url = segments[0]
                anchor = ''
            return tag.a(label, href=(url and formatter.href.qa(url) or '') \
                    + (anchor and '#' + anchor or ''))

    # Utility methods used by other modules
    def get_qainfotext(self):
        """ Retrieves the QA info text in sidebar from database. """
        try:
            cnx = self.env.get_db_cnx()
            cursor = cnx.cursor()
            cursor.execute("SELECT value from system " \
                "WHERE name='qa_infotext'")
            rows = cursor.fetchall()
            if rows:
                return rows[0][0] # Only item in cursor (hopefully)
            else:
                return ''
        except:
            return ''

    def set_qainfotext(self, text=''):
        """ Stores the QA info text in the database. """
        try:
            cnx = self.env.get_db_cnx()
            cursor = cnx.cursor()
            cursor.execute("UPDATE system set value=%s " \
                "WHERE name=%s", (text, 'qa_infotext'))
            cnx.commit()
            return True
        except:
            return False

    # CRUD methods that support input verification and listener and manipulator APIs
    def create_post(self, req, bp, version_author, version_comment=u'', verify_only=False):
        """ Creates a new post, or a new version of existing post.
        Does some input verification.
        Supports manipulator and listener plugins.
        Returns [] for success, or a list of (field, message) tuples if not."""
        warnings = []
        # Do basic checking for content existence
        warnings.extend(bp.save(version_author, version_comment, verify_only=True))
        # Check if any plugins has objections with the contents
        fields = {
            'title': bp.title,
            'body': bp.body,
            'author': bp.author,
            'version_comment': version_comment,
            'version_author': version_author,
            'categories': bp.categories,
            'category_list': bp.category_list}
        
        for manipulator in self.manipulators:
            warnings.extend(manipulator.validate_test_case(
                            req, bp.name, bp.version, fields))
        if warnings or verify_only:
            return warnings
        
        # All seems well - save and notify
        warnings.extend(bp.save(version_author, version_comment))
        
        for listener in self.listeners:
            listener.test_case_changed(bp.name, bp.version)
        
        return warnings
        
    def create_comment(self, req, bc, verify_only=False):
        """ Create a comment. Comment and author set on the bc (comment) instance:
        * Calls manipulators and bc.create() (if not verify_only) collecting warnings
        * Calls listeners on success
        Returns [] for success, or a list of (field, message) tuples if not."""
        # Check for errors
        warnings = []
        # Verify the basics such as content existence, duplicates, post existence
        warnings.extend(bc.create(verify_only=True))
        # Now test plugins to see if new issues are raised.
        fields = {'comment': bc.comment,
                  'author': bc.author}
        for manipulator in self.manipulators:
            warnings.extend(
                manipulator.validate_test_case_comment(req, bc.post_name, fields))
        if warnings or verify_only:
            return warnings
        # No problems (we think), try to save.
        warnings.extend(bc.create())
        if not warnings:
            for listener in self.listeners:
                listener.test_case_comment_added(bc.post_name, bc.number)
        return warnings
    
    def delete_comment(self, bc):
        """ Deletes the comment (bc), and notifies listeners.
        Returns [] for success, or a list of (field, message) tuples if not."""
        warnings = []
        fields = {'post_name': bc.post_name,
                  'number': bc.number,
                  'comment': bc.comment,
                  'author': bc.author,
                  'time': bc.time}
        is_deleted = bc.delete()
        if is_deleted:
            for listener in self.listeners:
                listener.test_case_comment_deleted(
                        fields['post_name'], fields['number'], fields)
        else:
            warnings.append(('', "Unknown error. Not deleted."))
        return warnings

    def get_qa_authors(self):
        possible_owners = []
        for user in PermissionSystem(self.env).get_users_with_permission('QA_MODIFY'):
            possible_owners.append(user)
        return possible_owners

	# Internal methods
