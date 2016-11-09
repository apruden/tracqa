INSERT INTO qa_testplan (title, description) VALUES ('test plan 1' , 'Some test plan 1');
INSERT INTO qa_testplan (title, description) VALUES ('test plan 2' , 'Some test plan 2');
INSERT INTO qa_testplan (title, description) VALUES ('test plan 3' , 'Some test plan 3');
INSERT INTO qa_testplan (title, description) VALUES ('test plan 4' , 'Some test plan 4');
INSERT INTO qa_testplan (title, description) VALUES ('test plan 5' , 'Some test plan 5');

INSERT INTO qa_testrun (testplan_id, title, description) VALUES (1, 'test runs 1-1', 'Some test run 1-1');
INSERT INTO qa_testrun (testplan_id, title, description) VALUES (1, 'test runs 1-2', 'Some test run 1-2');
INSERT INTO qa_testrun (testplan_id, title, description) VALUES (2, 'test runs 2-1', 'Some test run 2-1');
INSERT INTO qa_testrun (testplan_id, title, description) VALUES (2, 'test runs 2-2', 'Some test run 2-2');

INSERT INTO qa_testsuite (title, description) VALUES ('test suite 1', 'some test suite 1');
INSERT INTO qa_testsuite (title, description) VALUES ('test suite 2', 'some test suite 2');
INSERT INTO qa_testsuite (title, description) VALUES ('test suite 3', 'some test suite 3');

INSERT INTO qa_testcase (testsuite_id, isnegative,  title, steps, acceptance) VALUES (1, 0, 'test case 1', 'step 1 step 2 step 3', 'acceptance 1');
INSERT INTO qa_testcase (testsuite_id, isnegative,  title, steps, acceptance) VALUES (1, 0, 'test case 2', 'step 1 step 2 step 3', 'acceptance 1');
INSERT INTO qa_testcase (testsuite_id, isnegative,  title, steps, acceptance) VALUES (1, 0, 'test case 3', 'step 1 step 2 step 3', 'acceptance 1');
INSERT INTO qa_testcase (testsuite_id, isnegative,  title, steps, acceptance) VALUES (2, 0, 'test case 4', 'step 1 step 2 step 3', 'acceptance 1');
INSERT INTO qa_testcase (testsuite_id, isnegative,  title, steps, acceptance) VALUES (2, 0, 'test case 5', 'step 1 step 2 step 3', 'acceptance 1');
INSERT INTO qa_testcase (testsuite_id, isnegative,  title, steps, acceptance) VALUES (3, 0, 'test case 6', 'step 1 step 2 step 3', 'acceptance 1');

INSERT INTO qa_tp_tc_rel (testplan_id, testcase_id) VALUES (1, 1);
INSERT INTO qa_tp_tc_rel (testplan_id, testcase_id) VALUES (1, 2);
INSERT INTO qa_tp_tc_rel (testplan_id, testcase_id) VALUES (1, 3);
INSERT INTO qa_tp_tc_rel (testplan_id, testcase_id) VALUES (2, 4);
INSERT INTO qa_tp_tc_rel (testplan_id, testcase_id) VALUES (2, 5);
INSERT INTO qa_tp_tc_rel (testplan_id, testcase_id) VALUES (3, 6);
