import datetime
import unittest

from trac.test import EnvironmentStub, Mock
from tracqa.db import QaSetup
from tracqa.model import *

class GetTestPlans(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        QaSetup(self.env).upgrade_environment(self.env.get_db_cnx())

    def tearDown(self):
        self.env.destroy_db()
        del self.env

    def test_save(self):
        # 2 posts in one period
        testplan = TestPlan(self.env)
        testplan.title = "test"
        testplan.description = "test"
        testplan.save()
        self.assertEquals([], tesplan.tpid)
        
suite = unittest.TestLoader().loadTestsFromTestCase(GetTestPlans)
unittest.TextTestRunner(verbosity=2).run(suite)
