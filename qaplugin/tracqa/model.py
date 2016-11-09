# -*- coding: utf-8 -*-
"""
Entity models supporting the basic features of the plugin.
 * CRUD code - create, read, update and delete.
 * Various get and search util function for getting lists of items

License: BSD

(c) 2010
"""
import pdb
import datetime
import string, new
from types import *
from trac.attachment import Attachment
from trac.resource import Resource
from trac.search import search_to_sql
from trac.util.datefmt import to_datetime, to_timestamp, utc

try:
    from trac.util.compat import itemgetter
    from trac.util.compat import sorted, set
except ImportError:
    from operator import itemgetter

__all__ = ['TestCase',
        'TestSuite',
        'TestPlan',
        'Assignment',
        'Execution',
        'TestRun',
        'search_testcases',
        'get_testcases_grouped',
        'get_testcases_resources',
        'get_testcases_by_testplan',
        'get_testcases_by_testrun',
        'get_testcases_report',
        'get_next_assigned_testcase',
        'add_testplans_testcases_rel',
        'TestCaseGroup']

bag_belongs_to, bag_has_many = [], []
def belongs_to(what): bag_belongs_to.append(what)
def has_many(what): bag_has_many.append(what)

def required_validator(ins, fields):
    errors = []
    for f in fields:
        try:
            if not getattr(ins,f):
                errors.append('%s is required' % f)
        except AttributeError:
            errors.append('%s is required' % f)
    return errors


def strlen_validator(ins, rules):
    errors = []
    for rule in rules:
        try:
            if len(getattr(ins, rule[0])) > rule[1]:
                errors.append('Value for %s should be less than %s' % (rule[0], rule[1]))
        except AttributeError:
            pass
    return errors


validators = { 'required' : required_validator, 'strlen' : strlen_validator }



############### Public functions ##########################

def search_testcases(env, terms):
    """ Free text search for content of blog posts.
    Input is a list of terms.
    Returns a list of tuples with: ( ... ) """

    cnx = env.get_db_cnx()
    cursor = cnx.cursor()
    columns = ['title', 'description', 'author', 'acceptance']
    search_clause, args = search_to_sql(cnx, columns, terms)
    sql = """
        SELECT author, title, description
        FROM  qa_testcase
        WHERE """ + search_clause
    env.log.debug("search_testcases() SQL: %r" % sql)
    cursor.execute(sql, args)

    return [(row[0], row[1], to_datetime(row[2], utc), row[3], \
            row[4], row[5]) for row in cursor]


def get_next_assigned_testcase(env, author, trid):
    cnx = env.get_db_cnx()
    cursor = cnx.cursor()
    sql = """ 
        SELECT tc.id FROM qa_testcase tc
        JOIN qa_assignment a1 ON a1.testcase_id = tc.id
        LEFT OUTER JOIN qa_execution ex ON ex.testrun_id = a1.testrun_id AND ex.testcase_id = a1.testcase_id
        WHERE a1.author = %s AND a1.testrun_id = %s AND ( ex.result IS NULL OR ex.result = 0 )
        ORDER BY tc.testsuite_id DESC LIMIT 1"""
    cursor.execute(sql, (author, trid))
    temp = cursor.fetchone()
    if temp:
        return temp[0]
    return None


def get_testcases_resources(env):
    """ Returns a list of resource instances of existing blog posts (current
    version). The list is ordered by publish_time (newest first). """
    cnx = env.get_db_cnx()
    cursor = cnx.cursor()
    sql = """SELECT title FROM qa_testcase ORDER BY id DESC"""
    cursor.execute(sql)
    qa_realm = Resource('qa')
    return [qa_realm(id=post[0], version=0) for post in cursor]


def add_testplans_testcases_rel(env, tpid=0, tcid=0):
    """ add test case to test plans """
    cnx = env.get_db_cnx()
    cursor = cnx.cursor()
    sql = """
        INSERT INTO qa_tp_tc_rel (testplan_id, testcase_id) VALUES (%s, %s)"""
    try:
        cursor.execute(sql, (tpid, tcid))
        cnx.commit()
    except:
        pass

def get_testcases_by_testplan(env, tpid=0, limit=50, offset=0):
    """ get testcases by testplan """
    cnx = env.get_db_cnx()
    cursor = cnx.cursor()

    sql = """
        SELECT COUNT(*)
        FROM qa_testplan tp
        JOIN qa_tp_tc_rel rel ON tp.id = rel.testplan_id
        JOIN qa_testcase tc ON rel.testcase_id = tc.id
        WHERE tp.id = %s"""
    cursor.execute(sql, (tpid,))
    count = cursor.fetchone()[0]

    sql = """
        SELECT tc.id, tc.title, tc.steps, tc.testsuite_id
        FROM qa_testplan tp
        JOIN qa_tp_tc_rel rel ON tp.id = rel.testplan_id
        JOIN qa_testcase tc ON rel.testcase_id = tc.id
        WHERE tp.id = %s ORDER BY tc.testsuite_id LIMIT %s OFFSET %s"""
    cursor.execute(sql, (tpid, limit, offset))
    group_dict = {}

    for row in cursor:
        testsuite_id = row[3]
        if not testsuite_id:
            testsuite_id = 0
            if not testsuite_id in group_dict:
                group_dict[0] = TestCaseGroup(0,"Others")
        if not testsuite_id in group_dict:
            testsuite = TestSuite.findone(env, testsuite_id, fields=['title'])
            group_dict[testsuite_id] = TestCaseGroup(testsuite.id, testsuite.title)
        group_dict[testsuite_id].add_testcase(DynamicDictionary(id = row[0],
            title =  row[1], steps = row[2]))

    return group_dict, count

def get_testcases_grouped(env, testsuite_id = 0, limit = 50, offset = 0):
    """ get testcases grouped """
    cnx = env.get_db_cnx()

    cursor = cnx.cursor()
    sql = """
        SELECT COUNT(*)
        FROM qa_testcase"""

    if testsuite_id:
        sql = '%s %s' % (sql, 'WHERE testsuite_id = %s')
        cursor.execute(sql, (testsuite_id,))
    else:
        cursor.execute(sql)
    count = cursor.fetchone()[0]

    sql = """
        SELECT id, title, testsuite_id
        FROM qa_testcase"""

    if testsuite_id:
        sql = '%s %s' % (sql, 'WHERE testsuite_id = %s')

    sql = '%s %s' % (sql,'ORDER BY testsuite_id DESC LIMIT %s OFFSET %s')

    if testsuite_id:
        cursor.execute(sql, (testsuite_id, limit, offset))
    else:
        cursor.execute(sql, (limit, offset))
    group_dict = {}

    for row in cursor:
        testsuite_id = row[2]
        if not testsuite_id:
            testsuite_id = 0
            if not testsuite_id in group_dict:
                group_dict[0] = TestCaseGroup(0,"Others")
        if not testsuite_id in group_dict:
            testsuite = TestSuite.findone(env, testsuite_id, fields=['title'])
            group_dict[testsuite_id] = TestCaseGroup(testsuite.id, testsuite.title)
        group_dict[testsuite_id].add_testcase(DynamicDictionary(id = row[0],
            title =  row[1]))

    return group_dict, count


def get_testcases_by_testrun(env, trid=0, limit = 50, offset = 0):
    """ get testcases by testplan """
    cnx = env.get_db_cnx()

    cursor = cnx.cursor()
    sql = """
        SELECT COUNT(*)
        FROM qa_testrun tr
        JOIN qa_testplan tp ON tp.id = tr.testplan_id
        JOIN qa_tp_tc_rel rel ON rel.testplan_id = tp.id
        WHERE tr.id = %s"""
    cursor.execute(sql, (trid,))
    count = cursor.fetchone()[0]

    sql = """
        SELECT tc.id, tc.title, tc.steps, a.author, tc.testsuite_id
        FROM qa_testrun tr
        JOIN qa_testplan tp ON tp.id = tr.testplan_id
        JOIN qa_tp_tc_rel rel ON rel.testplan_id = tp.id
        JOIN qa_testcase tc ON tc.id = rel.testcase_id
        LEFT OUTER JOIN qa_assignment a ON a.testcase_id = tc.id AND a.testrun_id = tr.id
        WHERE tr.id = %s ORDER BY tc.testsuite_id LIMIT %s OFFSET %s"""
    cursor.execute(sql, (trid, limit, offset))
    group_dict = {}

    for row in cursor:
        testsuite_id = row[4]
        if not testsuite_id:
            testsuite_id = 0
            if not testsuite_id in group_dict:
                group_dict[0] = TestCaseGroup(0,"Others")
        if not testsuite_id in group_dict:
            testsuite = TestSuite.findone(env, testsuite_id, fields=['title'])
            group_dict[testsuite_id] = TestCaseGroup(testsuite.id, testsuite.title)
        group_dict[testsuite_id].add_testcase(DynamicDictionary(id = row[0],
            title =  row[1], steps = row[2], author = row[3]))

    return group_dict, count


def get_testcases_report(env, assigned_author='', trid = 0, tsid = 0, result = None):
    """ get tc by testrun """
    cnx = env.get_db_cnx()
    cursor = cnx.cursor()
    sql = """
        SELECT tc.id, tc.testsuite_id, tc.title, tr.id, a1.author, ex.author, ex.time, ex.result 
        FROM qa_testrun tr
        JOIN qa_tp_tc_rel rel ON tr.testplan_id = rel.testplan_id
        JOIN qa_testcase tc ON tc.id = rel.testcase_id
        LEFT OUTER JOIN qa_assignment a1 ON a1.testcase_id = tc.id AND a1.testrun_id = tr.id
        LEFT OUTER JOIN qa_execution ex ON ex.testcase_id = tc.id AND ex.testrun_id = tr.id
        WHERE tr.id = %s"""
    param = [trid]
    where = ''
    if assigned_author:
        where = where + ' AND a1.author = %s '
        param.append(assigned_author)
    if result != None:
        where = where + ' AND ex.result = %s '
        param.append(result)
    if tsid:
        where = where + ' AND tc.testsuite_id = %s '
        param.append(tsid)

    sql = '%s %s' % (sql,where)
    cursor.execute(sql, param)
    test_cases = []
    for row in cursor:
        test_cases.append(DynamicDictionary(id=row[0], testsuite_id=row[1], title=row[2],  
            testrun_id = row[3], author_assigned = row[4], author_execution=row[5], time = row[6],
            result = row[7]))

    return test_cases


#******************** Classes ********************************
class MetaRecord(type):
    def __new__(cls, name, bases, dct):
        global bag_belongs_to, bag_has_many
        if name in globals(): return globals()[name]
        else:
            Record = type.__new__(cls, name, bases, dct)
            for i in bag_belongs_to: Record.belongs_to(i)
            for i in bag_has_many: Record.has_many(i)
            bag_belongs_to = []
            hag_has_many = []
            return Record


class ActiveRecordBase(dict):
    __metaclass__ = MetaRecord

    @classmethod
    def belongs_to(cls, what):
        def dah(self):
            belong_cls = globals().get(what,None)
            if not belong_cls:
                belong_cls = type(what,(ActiveRecordBase,),{})
            return belong_cls.find(self[what + '_id'])
        setattr(cls, what, new.instancemethod(dah, None, cls))

    @classmethod
    def has_many(cls, what):
        def dah(self):
            hasmany_cls = globals().get(what, None)
            if not hasmany_cls:
                hasmany_cls = type(what, (ActiveRecordBase,), {})
            return hasmany_cls.find_by_sql('SELECT * FROM %s WHERE %s = %s' % (
                string.lower('qa_' + hasmany_cls.__name__),
                string.lower(cls.__name__) + '_id',
                self['id']), [])
        setattr(cls, what, new.instancemethod(dah, None, cls))

    @classmethod
    def insert(cls, env, **kwds):
        vs = [[k, kwds[k]] for k in kwds]
        if vs:
            s = 'INSERT INTO %s (%s) VALUES (%s)' % (
                    string.lower('qa_' + cls.__name__), 
                    ', '.join([v[0] for v in vs]), 
                    ', '.join(['%s' for v in vs]))
            conn = env.get_db_cnx()
            cursor = conn.cursor()
            cursor.execute(s, [v[1] for v in vs])
            conn.commit()
            return conn.get_last_id(cursor,
                    string.lower('qa_' + cls.__name__))
        else: raise 'Nothing to insert.'

    @classmethod
    def find_by_sql(cls, env, sql, values):
        conn = env.get_db_cnx()
        cursor = conn.cursor()
        cursor.execute(sql, values)
        r = conn.fetchall() or []
        list = []
        for i in r:
            list.append(cls(i))
        return list

    @classmethod
    def findone(cls, env, *args, **kwargs):
        res = cls.find(env, *args, **kwargs)
        if len(res) > 0:
            return res[0]
        else:
            return None

    @classmethod
    def find(cls, env, *args, **kwargs):
        if len(args) == 1:
            return cls.findpaged(env, args[0], **kwargs)[0]
        else:
            return cls.findpaged(env, **kwargs)[0]

    @classmethod
    def findpaged(cls, env, *args, **kwargs):
        id = 0
        fields = []
        limit = 0
        offset = 0
        nr = 0
        where_fields = {}

        if len(args) == 1:
            id = args[0]
        
        for k in kwargs:
            if k == 'fields':
                fields = kwargs[k]
            elif k == 'limit':
                limit = kwargs[k]
            elif k == 'offset':
                offset = kwargs[k]
            else:
                where_fields[k] = kwargs[k]

        fields.insert(0, 'id')
        sfields = ', '.join(fields)
        swherefields = ' AND '.join([ '%s = %s' % (k,v) for (k,v) in where_fields.items()]);

        q = 'SELECT %s FROM %s' % (sfields, string.lower('qa_' + cls.__name__))
        qc = 'SELECT COUNT(*) FROM %s' % (string.lower('qa_' + cls.__name__),)
        where = ''
        slimit = ''
        soffset = ''
        if id:
            where = ' WHERE id = %s' % (id,)
        if where_fields:
            if where:
                where = '%s AND %s' % (where,swherefields)
            else:
                where = ' WHERE %s' % (swherefields,)
        if limit > 0:
            slimit = ' LIMIT %s' % (limit,)
        if offset > 0:
            soffset = ' OFFSET %s' % (offset,)

        conn = env.get_db_cnx()
        cursor = conn.cursor()

        if id == 0 and limit > 0:
            cursor.execute(qc + where)
            nr = cursor.fetchone()[0]

        cursor.execute(q + where + slimit + soffset)
        r = cursor.fetchall() or []
        list = []
        for i in r:
            list.append(cls(dict(zip(fields, i))))
        
        if nr == 0:
            nr = len(list)

        return list, nr 

    @classmethod
    def update(cls, env, id, **kwds):
        vs = [[k, kwds[k]] for k in kwds]
        if vs:
            s = 'UPDATE %s SET %s WHERE id=%s' % ( 'qa_' + string.lower(cls.__name__),
                 ', '.join(['%s=%%s' % (v[0]) for v  in vs]), id)
            conn = env.get_db_cnx()
            cursor = conn.cursor()
            cursor.execute(s, [v[1] for v in vs] )
            conn.commit()

    @classmethod
    def delete(cls, env, id):
        conn = env.get_db_cnx()
        cursor = conn.cursor()
        s = 'DELETE FROM %s WHERE id = %%s' % ('qa_' + string.lower(cls.__name__),)
        cursor.execute(s, [id])
        conn.commit()

    def __init__(self, dct = {}):
        dict.__init__(self, dct)
        self.__dict__['cur_table'] = string.lower('qa_' + self.__class__.__name__)
        self.__dict__['where'] = ''
        self.__dict__['sql_buff'] = {}

    def save(self, env):
        s = ''
        i = []

        if self.id:
            f = []
            for v in self.sql_buff:
                if v == 'id':
                    continue
                f.append('%s = %%s' % (v,))
                i.append(self.sql_buff[v])
            s = 'UPDATE %s SET %s WHERE id = %s' % (self.cur_table, ', '.join(f), self.id)
        else:
            f=[]
            for v in self.sql_buff:
                if v == 'id':
                    continue
                f.append(v)
                i.append(self.sql_buff[v])
                if f and i:
                    s = 'INSERT INTO %s (%s) VALUES (%s)' % (
                            self.cur_table,
                            ', '.join(f), 
                            ', '.join(['%s' for tmp in i]))

        if s:
            conn = env.get_db_cnx()
            cursor = conn.cursor()
            cursor.execute(s, i)
            conn.commit()
        else: raise 'Nothing to insert.'

    def is_valid(self):
        errors = []
        for k in self.__class__.rules:
            errors.extend(validators[k](self, self.__class__.rules[k]))
        return errors

    def __setattr__(self, attr, value):
        if attr in self.__dict__: self.__dict__[attr] = value
        else:
            v = value
            self.__dict__['sql_buff'][attr] = v
            self[attr] = v

    def __getattr__(self,attr):
        if attr in self.__dict__: return self.__dict__[attr]
        try: return self[attr]
        except KeyError: pass


class TestCase(ActiveRecordBase):

    rules = { 'required' : ['title' , 'description'] ,
            'strlen' : [['title', 150]]}

    def __init__(self, dct = {}):
        super(TestCase, self).__init__(dct)


class TestSuite(ActiveRecordBase):

    rules = { 'required' : ['title' , 'description'] ,
        'strlen' : [['title', 150]]}

    def __init__(self, dct = {}):
        super(TestSuite, self).__init__(dct)


class TestRun(ActiveRecordBase):
    rules = { 'required' : ['title' , 'description'] ,
        'strlen' : [['title', 150]]}

    belongs_to('TestPlan')

    def __init__(self, dct = {}):
        super(TestRun, self).__init__(dct)


class Execution(ActiveRecordBase):

    def __init__(self, dct={}):
        super(Execution, self).__init__(dct)


class Assignment(ActiveRecordBase):

    def __init__(self, dct={}):
        super(Assignment, self).__init__(dct)


class TestPlan(ActiveRecordBase):
    rules = { 'required' : ['title' , 'description'] ,
        'strlen' : [['title', 150]]}

    def __init__(self, dct = {}):
        super(TestPlan, self).__init__(dct)


class DynamicDictionary(dict):

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __getattr__(self, name):
        return self[name]


class TestCaseGroup:

    def __init__(self, id, title):
        self.id = id
        self.title = title
        self.testcases = []

    def add_testcase(self, testcase):
        self.testcases.append(testcase)
