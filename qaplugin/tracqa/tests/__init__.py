
from unittest import TestSuite, makeSuite

def test_suite():
    suite = TestSuite()
    import tracqa.tests.model
    suite.addTest(makeSuite(tracqa.tests.model.GetTestPlans))
    return suite
