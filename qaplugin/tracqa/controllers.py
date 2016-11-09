import pdb
import datetime

from trac.attachment import Attachment
from trac.resource import Resource
from trac.search import search_to_sql
from trac.util.translation import _
from trac.util import as_int
from trac.util.datefmt import format_datetime, format_time, from_utimestamp,\
        to_datetime, to_timestamp, utc
from trac.util.presentation import Paginator
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
        add_stylesheet, add_link, add_script, add_warning, \
        add_notice, add_ctxtnav, prevnext_nav
from model import *
from core import *
from trac.perm import IPermissionRequestor, PermissionCache, PermissionSystem

__all__ = ['TestPlanController',
        'TestCaseController',
        'TestSuiteController',
        'TestRunController',
        'ExecutionController',
        'AssignmentController',
        'ReportController']

class ControllerBase(object):

    def __init__(self, env, req):
        self.env = env
        self.req = req

    def build_paginator(self, results, page, limit, total, action):
        items = results
        if not results:
            items = range(0, limit)
        paginator = Paginator(items, page - 1, limit, total)
        def report_href(**kwargs):
            params = {}
            params['page'] = page
            if limit:
                params['max'] = limit
            params.update(kwargs)
            return self.req.href.qa(action, params)
        if paginator.has_next_page:
            add_link(self.req, 'next', report_href(page=page + 1),
                    _('Next Page'))
        if paginator.has_previous_page:
            add_link(self.req, 'prev', report_href(page=page - 1),
                    _('Previous Page'))
        pagedata = []
        shown_pages = paginator.get_shown_pages(21)
        for p in shown_pages:
            pagedata.append([report_href(page=p), None, str(p),
                _('Page %(num)d', num=p)])
        fields = ['href', 'class', 'string', 'title']
        paginator.shown_pages = [dict(zip(fields, p)) for p in pagedata]
        paginator.current_page = { 'href' : None,
                'class': 'current',
                'string' : str(paginator.page + 1),
                'title': None }
        #p = max is not None and page or None
        return paginator


class ExecutionController(object):

    def __init__(self, env, req):
        self.env = env
        self.req = req

    def add(self, *args):
        if self.req.method == 'POST':
            author = "%s" % (self.req.args.get('author'),)
            testrun_id = self.req.args.get('testrun_id')
            testcase_id = self.req.args.get('testcase_id')
            execution = Execution.findone(self.env, author = ("'%s'" % (author,)), testrun_id = testrun_id, testcase_id = testcase_id)
            if not execution:
                execution = Execution()
            execution.author = author
            execution.testrun_id = testrun_id
            execution.testcase_id = testcase_id
            execution.defects = self.req.args.get('defects')
            result = self.req.args.get('result')
            if result == 'pass':
                execution.result = 1
            else:
                execution.result = 2
            execution.time = datetime.datetime.now(utc)
            execution.save(self.env)
            next_tcid = get_next_assigned_testcase(self.env, execution.author, execution.testrun_id)
            if next_tcid:
                self.req.redirect(self.req.href.qa('testcase/show', next_tcid) +
                        '?testrun_id=' + execution.testrun_id)
            else:
                self.req.redirect(self.req.href.qa('report/result'))


class AssignmentController(object):

    def __init__(self, env, req):
        self.env = env
        self.req = req

    def index(self, *args):
        author = self.req.authname
        self.req.redirect('%s?%s=%s',(self.req.href.qa('report/result'),'author',author))

    def add(self, *args):
        if self.req.method == 'POST':
            assignment = Assignment(self.env)
            assignment.author = self.req.args.get('author')
            assignment.testrun_id = self.req.args.get('testrun_id')
            assignment.save(self.env)
            self.req.redirect(self.req.href.qa())


class TestPlanController(ControllerBase):

    def __init__(self, env, req):
        self.env = env
        self.req = req

    def show(self, id):
        template = 'qa_tp_view.html'
        page = int(self.req.args.get('page', '1'))
        default_max = 50
        max = self.req.args.get('max')
        limit = as_int(max, default_max, min=0)
        offset = (page - 1) * limit
        data = {}
        data['tp'] = TestPlan.findone(self.env, id, fields=['title', 'description'])
        data['ts_list'] = TestSuite.find(self.env, fields=['title'])
        testcases, count = get_testcases_by_testplan(self.env, id, limit, offset)
        data['tc_groups']  = testcases
        data['paginator'] = self.build_paginator([], page, limit, count, '%s/%s' % ('testplan/show', id))  
        return (template, data)

    def index(self, *args):
        template = 'qa_tp_index.html'
        data = {}
        data['tp_list'] = TestPlan.find(self.env, fields=['title'])
        return (template, data)

    def add(self, *args):
        data = {}
        data['is_create'] = True
        if self.req.method=='GET':
            template= 'qa_tp_edit.html'
            return (template, data)
        if self.req.method=='POST':
            tp = TestPlan()
            tp.title = self.req.args.get('title')
            tp.description = self.req.args.get('description')
            errors  = tp.is_valid()
            if not errors:
                tp.save(self.env)
                self.req.redirect(self.req.href.qa('testplan/index'))
            else:
                template= 'qa_tp_edit.html'
                data['errors'] = errors
                data['tp'] = tp
                return (template, data)

    def edit(self, id):
        data = {}
        data['is_create'] = False
        if self.req.method=='GET':
            template= 'qa_tp_edit.html'
            data['tp'] = TestPlan.findone(self.env, id, fields=['title', 'description'])
            return (template, data)
        if self.req.method == 'POST':
            tp = TestPlan.findone(self.env, id)
            tp.title = self.req.args.get('title')
            tp.description = self.req.args.get('description')
            tp.save(self.env)
            self.req.redirect(self.req.href.qa('testplan/index'))

    def delete(self, id):
        if self.req.method == 'POST':
            self.req.perm(bp.resource).require('QA_ADMIN')
            TestPlan.delete(self.env, id)
            self.req.redirect(self.req.href.qa('testplan/index'))

    def add_testsuite(self, *args):
        testsuite_id = self.req.args.get('testsuite_id')
        testplan_id = self.req.args.get('testplan_id')
        tc_list = TestCase.find(self.env, testsuite_id = testsuite_id)
        for tc in tc_list:
            add_testplans_testcases_rel(self.env, testplan_id, tc.id)
        self.req.redirect(self.req.href.qa('testplan/show', testplan_id))


class TestRunController(ControllerBase):

    def __init__(self, env, req):
        super(TestRunController,self).__init__(env, req)

    def show(self, id):
        template = 'qa_tr_view.html'
        page = int(self.req.args.get('page', '1'))
        default_max = 50
        max = self.req.args.get('max')
        limit = as_int(max, default_max, min=0)
        offset = (page - 1) * limit
        data = {}
        testrun = TestRun.findone(self.env, id, fields=['title', 'description', 'testplan_id'])
        qacore = QaCore(self.env)
        data['tr'] = testrun
        data['author_list'] = qacore.get_qa_authors()
        tc_list, total = get_testcases_by_testrun(self.env, testrun.id, limit, offset)
        data['tc_list'] = tc_list
        data['paginator'] = self.build_paginator([], page, limit, total, '%s/%s' % ('testrun/show', id))
        return (template,data)

    def index(self, *args):
        template = 'qa_tr_index.html'
        data = {}
        data['tr_list'] = TestRun.find(self.env, fields=['title'])
        return (template, data)

    def add(self, *args):
        return self.edit(0, args)

    def edit(self, id = 0, *args):
        if self.req.method == 'GET':
            template = 'qa_tr_edit.html'
            data = {}
            if id != 0:
                data['tr'] = TestRun.findone(self.env, id, fields=['title', 'description'])
            data['tp_list'] = TestPlan.find(self.env, fields=['title'])
            data['is_create'] = (id == 0)
            data['create_dict'] = {'disabled' : (id!=0) and 'disabled' or None }
            return (template, data)

        if self.req.method == 'POST':
            if id != 0:
                tr = TestRun.findone(self.env, id)
            else:
                tr = TestRun()
            tr.testplan_id = self.req.args.get('testplan_id')
            tr.title = self.req.args.get('title')
            tr.description = self.req.args.get('description')
            tr.save(self.env)
            self.req.redirect(self.req.href.qa('testrun/index'))

    def delete(self, id):
        if self.req.method == 'POST':
            TestRun.delete(self.env, id)
            self.req.redirect(self.req.href.qa('testrun/index'))

    def assign_testcases (self, *args):
        testrun_id = self.req.args.get('testrun_id')
        author = self.req.args.get('author')
        tc_list = self.req.args.get('tc_list')
        for testcase_id in tc_list:
            assignment = Assignment.findone(self.env, testrun_id=testrun_id, testcase_id=testcase_id)
            if not assignment:
                assignment = Assignment()
                assignment.testrun_id = testrun_id
                assignment.testcase_id = testcase_id
            assignment.author = author
            assignment.save(self.env) 
        self.req.redirect(self.req.href.qa('testrun/show', testrun_id))


class TestSuiteController(ControllerBase):

    def __init__(self, env, req):
        super(TestSuiteController, self).__init__(env, req)

    def show(self, id):
        template = 'qa_ts_view.html'
        data = { 'paginator' : None }
        page = int(self.req.args.get('page', '1'))
        default_max = 50
        max = self.req.args.get('max')
        limit = as_int(max, default_max, min=0)
        offset = (page - 1) * limit
        data['ts'] = TestSuite.findone(self.env, id, fields=['title', 'description'])
        results, total = TestCase.findpaged(self.env, limit = limit, offset = offset, fields=['title'], testsuite_id = id)
        data['tc_list'] = results
        if limit > 0:
            data['paginator'] = self.build_paginator([], page, limit, total, '%s/%s' % ('testsuite/show', id))
        return (template,data)

    def index(self, *args):
        template = 'qa_ts_index.html'
        data = {}
        ts_list = TestSuite.find(self.env, fields=['title'])
        data['ts_list'] = ts_list
        return (template, data)

    def add(self, *args):
        return self.edit(0)

    def edit(self, id):
        if self.req.method=='GET':
            template= 'qa_ts_edit.html'
            data = {}
            if id > 0:
                data['ts'] = TestSuite.findone(self.env, id, fields=['title', 'description'])
                data['is_create'] = False
            else:
                data['is_create'] = True
            return (template, data)

        if self.req.method == 'POST':
            ts = None
            if id > 0:
                ts = TestSuite.findone(self.env, id)
            else:
                ts = TestSuite()
            ts.title = self.req.args.get('title').strip()
            ts.description = self.req.args.get('description').strip()
            errors = ts.is_valid()
            if not errors:
                ts.save(self.env)
                self.req.redirect(self.req.href.qa('testsuite/index'))
            else:
                template= 'qa_ts_edit.html'
                data = {}
                data['errors'] = errors
                data['ts'] = ts
                if id > 0:
                    data['is_create'] = False
                else:
                    data['is_create'] = True

            return (template, data)

    def delete(self, id):
        if self.req.method == 'POST':
            TestSuite.delete(self.env, id)
            self.req.redirect(self.req.href.qa('testsuite/index'))


class TestCaseController(ControllerBase):

    def __init__(self, env, req):
        super(TestCaseController, self).__init__(env, req)

    def index(self, *args):
        template = 'qa_tc_index.html'
        data = {}
        page = int(self.req.args.get('page', '1'))
        testsuite_id = int(self.req.args.get('testsuite_id','0'))
        default_max = 50
        max = self.req.args.get('max')
        limit = as_int(max, default_max, min=0)
        offset = (page - 1) * limit

        data = {'title' : 'Test Cases', 
                'description' : 'Some description',
                'max' : limit, 
                'args' : args, 
                'show_args_form' : False,
                'message' : None, 
                'paginator' : None ,
                'ts_list' : [],
                'testsuite_id' : testsuite_id}

        data['ts_list'] = TestSuite.find(self.env, fields=['title'])
        results, num_items = get_testcases_grouped(
                self.env,
                testsuite_id,
                limit = limit,
                offset = offset)
        data['tc_list'] = results
        if limit > 0:
            data['paginator'] = self.build_paginator([], page, limit, num_items, 'testcase/index')
            
        #try:
        #    self.req.session['query_href'] = \
        #            self.req.session['query_href'] = report_href()
        #    for var in ('query_constraints', 'query_time'):
        #        if var in self.req.session:
        #            del self.req.session[var]
        #except (ValueError, KeyError):
        #    pass

        #if set(data['args']) - set(['USER']):
        #    data['show_args_form'] = True
        #    add_script(self.req, 'common/js/folding.js')

        # if missing_args:
            # add_warning(self.req, _(
                # 'The following arguments are missing: %(args)s',
                # args=", ".join(missing_args)))
        return 'qa_tc_index.html', data

    def show(self, id):
        testrun_id = self.req.args.get('testrun_id')
        template = 'qa_tc_view.html'
        data = {}
        data['tc'] = TestCase.findone(self.env, id, fields=['title', 'steps', 'acceptance'])
        data['testrun_id'] = testrun_id
        data['author'] = self.req.authname
        if testrun_id:
            data['is_execute'] = True
            data['is_show'] = False
        else:
            data['is_execute'] = False
            data['is_show'] = True
        data['execution_list'] = Execution.find(self.env, testcase_id = id)
        
        return (template, data)

    def add(self, *args):
        if self.req.method=='GET':
            template= 'qa_tc_edit.html'
            data = {}
            data['is_create'] = True
            data['ts_list'] = TestSuite.find(self.env, fields=['title'])
            return (template,data)

        if self.req.method=='POST':
            tc = TestCase()
            tc.testsuite_id = self.req.args.get('testsuite_id')
            tc.title = self.req.args.get('title')
            tc.steps = self.req.args.get('steps')
            tc.acceptance = self.req.args.get('acceptance')
            tc.save(self.env)
            self.req.redirect(self.req.href.qa('testcase/index'))

    def edit(self, id):
        if self.req.method=='GET':
            template = 'qa_tc_edit.html'
            data = {}
            data['tc'] = TestCase.findone(self.env, id, fields=['title', 'steps', 'acceptance', 'testsuite_id'])
            data['ts_list'] = TestSuite.find(self.env, fields=['title'])
            data['is_create'] = False
            return (template, data)

        if self.req.method == 'POST':
            tc = TestCase.findone(self.env, id)
            tc.testsuite_id = self.req.args.get('testsuite_id')
            tc.title = self.req.args.get('title')
            tc.steps = self.req.args.get('steps')
            tc.acceptance = self.req.args.get('acceptance')
            tc.save(self.env)
            self.req.redirect(self.req.href.qa('testcase/index'))

    def delete(self, id):
        if self.req.method == 'POST':
            TestCase.delete(self.env, id)
            self.req.redirect(self.req.href.qa('testcase/index'))


class ReportController(ControllerBase):

    def __init__(self, env, req):
        super(ReportController,self).__init__(env, req)

    def result(self, *args):
        user = self.req.args.get('author')
        testrun_id = int(self.req.args.get('testrun_id') or 0)
        testsuite_id = int(self.req.args.get('testsuite_id') or 0)
        result_id = None
        if self.req.args.get('status'):
            result_id = int(self.req.args.get('status')[0] or 0)
        template = 'qa_tc_report.html'
        page = int(self.req.args.get('page', '1'))
        default_max = 20
        max = self.req.args.get('max')
        limit = as_int(max, default_max, min=0)
        offset = (page - 1) * limit

        data = {'title' : 'Test Cases',
                'description' : 'Some description',
                'author' : user,
                'testrun_id' : testrun_id,
                'testsuite_id' : testsuite_id,
                'max' : limit,
                'args' : args,
                'show_args_form' : False,
                'message' : None,
                'paginator' : None }

        results = get_testcases_report(self.env, user, testrun_id, testsuite_id, result_id)
        res_list = {}

        for res in results:
            if not res_list.has_key(res.testsuite_id):
                res_list[res.testsuite_id] = []
                temp = TestSuite.findone(self.env, testsuite_id, fields = ['title'])
                res_list[res.testsuite_id].append(temp)
                res_list[res.testsuite_id].append([res])
            else:
                res_list[res.testsuite_id][1].append(res)
        
        num_items = 1
        data['res_list'] = res_list
        testrun_list =  TestRun.find(self.env, fields = ['title'])
        data['tr_list'] = testrun_list
        testsuite_list =  TestSuite.find(self.env, fields = ['title'])
        data['ts_list'] = testsuite_list
        data['result_list'] = [0,1,2]  # 0: not run, 1: success, 2: failed
        qacore = QaCore(self.env)
        data['author_list'] = qacore.get_qa_authors()
        if limit > 0:
            data['paginator'] = self.build_paginator([], page, limit, num_items, 'report/result')

        #try:
        #    self.req.session['query_href'] = \
        #            self.req.session['query_href'] = report_href()
        #    for var in ('query_constraints', 'query_time'):
        #        if var in self.req.session:
        #            del self.req.session[var]
        #except (ValueError, KeyError):
        #    pass

        #if set(data['args']) - set(['USER']):
        #    data['show_args_form'] = True
        #    add_script(self.req, 'common/js/folding.js')

        return template, data
