# -*- coding: utf-8 -*-
"""
Interface code for the plugin.
Various providers for menus and request handling.

(c) 2010
"""
import datetime
import re
from pkg_resources import resource_filename
from genshi.builder import tag
from trac.attachment import AttachmentModule
from trac.config import ListOption, BoolOption, IntOption
from trac.core import *
from trac.mimeview.api import Context
from trac.resource import Resource
from trac.search.api import ISearchSource, shorten_result
from trac.timeline.api import ITimelineEventProvider
from trac.util import arity
from trac.util.datefmt import utc
from trac.util.text import shorten_line
from trac.util.translation import _
from trac.web.api import IRequestHandler, HTTPNotFound
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
        add_stylesheet, add_link, add_warning, add_notice, add_ctxtnav, prevnext_nav
from trac.wiki.formatter import format_to

try:
    from trac.util.compat import itemgetter
    from trac.util.compat import sorted, set
except ImportError:
    from operator import itemgetter

# Imports from same package
from model import *
from controllers import *
from core import QaCore
from util import map_month_names, parse_period

__all__ = ['QaModule']

class QaModule(Component):

    implements(INavigationContributor,
               ITemplateProvider,
               IRequestHandler)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'tracqa'

    def get_navigation_items(self, req):
        if 'QA_VIEW' in req.perm('qa'):
            yield ('mainnav', 'Qa',
                   tag.a(_('QA'), href=req.href.qa()) )

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        """ Makes the 'htdocs' folder inside the egg available. """
        return [('tracqa', resource_filename('tracqa', 'htdocs'))]

    def get_templates_dirs(self):
        """ Location of Trac templates provided by plugin. """
        return [resource_filename('tracqa', 'templates')]

    # IRequestHandler methods
    
    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        match = re.match(r'^/qa(?:/(.*)|$)', req.path_info)
        if match:
            req.args['qa_path'] = ''
            if match.group(1):
                req.args['qa_path'] = match.group(1)
            return True

    def process_request(self, req):
        """ Processing the request. """
        req.perm('qa').assert_permission('QA_VIEW')
        qa_core = QaCore(self.env)
        entity, action, pagename, path_items = self._parse_path(req)
        data = {}
        template = None
        #data['qa_infotext'] = qa_core.get_qainfotext()
        self.env.log.debug(
            "QA debug: entity=%r, action=%r, pagename=%r, path_items=%r" % (
                entity, action, pagename, path_items))

        if not entity:
            entity='report'
            action='result'
        
        controller_dict = { 'testplan' : 'TestPlanController',
            'testrun' : 'TestRunController',
            'testcase' : 'TestCaseController',
            'testsuite' : 'TestSuiteController',
            'execution' : 'ExecutionController',
            'assignment' : 'AssignmentController',
            'report' : 'ReportController'}
        
        if globals()[controller_dict[entity]]:
            controller = globals()[controller_dict[entity]](self.env, req)
            if hasattr(controller, action):
                action_method = getattr(controller, action)
                template, data = action_method(pagename)
            else:
                raise HTTPNotFound("Not a valid QA path.")
        else:
            raise HTTPNotFound("Not a valid QA path.")

        if 'QA_CREATE' in req.perm('qa'):
            add_ctxtnav(req, 'Test Plans', href=req.href.qa('/testplan/index'),
                    title="Test Plans")
            add_ctxtnav(req, 'Test Runs', href=req.href.qa('/testrun/index'),
                    title="Test Runs")
            add_ctxtnav(req, 'Test Suites', href=req.href.qa('/testsuite/index'),
                    title="Test Suites")
            add_ctxtnav(req, 'Test Cases', href=req.href.qa('/testcase/index'),
                    title="Test Cases")
            add_ctxtnav(req, 'Reports', href=req.href.qa('/report/result'),
                    title="Reports")

        add_stylesheet(req, 'tracqa/css/tracqa.css')
        add_stylesheet(req, 'common/css/admin.css')
        add_stylesheet(req, 'common/css/report.css')

        return (template, data, None)
    
    # Internal methods
    def _parse_path(self, req):
        """ Parses the request path for the qa and returns a
        ('entity', 'command', 'pagename', 'path_items') tuple. """
        
        # Parse out the path and actions from args
        path = req.args.get('qa_path', '')
        path_items = path.split('/')
        path_items = [item for item in path_items if item] # clean out empties
        entity = command = pagename = ''
        
        if not path_items:
            pass # emtpy default for return is fine
        elif len(path_items) > 2:
            entity = path_items[0].lower()
            command = path_items[1].lower()
            pagename = '/'.join(path_items[2:])
        elif len(path_items) > 1:
            entity = path_items[0].lower()
            command = path_items[1].lower()
            pagename = '/'.join(path_items[1:])
        else:
            entity = 'report'
            command = 'result'
            pagename = path
            
        return (entity, command, pagename, path_items)
