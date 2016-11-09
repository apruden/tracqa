import datetime
import unittest

from trac.test import EnvironmentStub, Mock
from tracqa.db import QaSetup
from tracqa.model import *

class GetTestPlans(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        QaSetup(self.env).upgrade_environment(self.env.get_db_cnx())
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        sql = "INSERT INTO qa_testsuite(title, description) VALUES (%s, %s)"
        cursor.execute(sql, ['tata', 'tete'])
        cnx.commit()

    def tearDown(self):
        self.env.destroy_db()
        del self.env

    #def test_find_testplans(self):
    #    dummy = TestPlan( { 'title' : 'toto title', 'description' : 'toto descr'})
    #    dummy.title = 'test title'
    #    dummy.description = 'test description'
    #    dummy.save(self.env)
    #    self.assertEquals(dummy.tpid, 0)

    @unittest.skip("demonstrating skipping")
    def test_get_testsuites(self):
        res = TestSuite.find(self.env, fields = ['title', 'description'])
        self.assertEquals(len(res), 1)

    def test_invalid_testcase_shows_error(self):
        tc = TestCase()
        tc.description = 'test'
        errors =  tc.is_valid()
        self.assertEquals(len(errors),1)
        
suite = unittest.TestLoader().loadTestsFromTestCase(GetTestPlans)
unittest.TextTestRunner(verbosity=2).run(suite)
