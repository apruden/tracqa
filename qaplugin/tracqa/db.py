# -*- coding: utf-8 -*-
"""
TracQaPlugin: The code managing the database setup and upgrades.

(c) 2010
"""

from trac.core import *
from trac.db.schema import Table, Column, Index
from trac.env import IEnvironmentSetupParticipant

__all__ = ['QaSetup']

# Database version identifier for upgrades.
db_version = 1

# Database schema
schema = [
        Table('qa_testplan', key=('id'))[
            Column('id', type='int', auto_increment=True),
            Column('title'),
            Column('description')],
        Table('qa_testsuite', key=('id'))[
            Column('id', type='int', auto_increment=True),
            Column('title'),
            Column('description')],
        Table('qa_tp_tc_rel', key=('id'))[
            Column('id', type='int', auto_increment=True),
            Column('testplan_id', type='int'),
            Column('testcase_id', type='int'),
            Index(['testplan_id', 'testcase_id'], unique=True)],
        Table('qa_testrun', key=('id'))[
            Column('id', type='int', auto_increment=True),
            Column('testplan_id', type='int'),
            Column('active', type = 'int'),
            Column('title'),
            Column('description'),
            Index(['testplan_id'])],
        Table('qa_testcase', key=('id'))[
            Column('id', type='int', auto_increment=True),
            Column('testsuite_id', type='int'),
            Column('isnegative', type='int'),
            Column('title'),
            Column('steps'),
            Column('acceptance'),
            Index(['testsuite_id'])],
        Table('qa_assignment', key=('id'))[
            Column('id', type='int', auto_increment=True),
            Column('testrun_id', type='int'),
            Column('testcase_id', type='int'),
            Column('author'),
            Index(['author']),
            Index(['testrun_id'])],
        Table('qa_execution', key=('id'))[
            Column('id', type='int', auto_increment=True),
            Column('testrun_id', type='int'),
            Column('testcase_id', type='int'),
            Column('version'),
            Column('defects'),
            Column('author'),
            Column('time', type='int'),
            Column('result'),
            Index(['time']),
            Index(['result']),
            Index(['author']),
            Index(['testrun_id']),
            Index(['testcase_id'])]]

# Create tables

def to_sql(env, table):
    """ Convenience function to get the to_sql for the active connector."""
    from trac.db.api import DatabaseManager
    dc = DatabaseManager(env)._get_connector()[0]
    return dc.to_sql(table)

def create_tables(env, db):
    """ Creates the basic tables as defined by schema.
    using the active database connector. """
    cursor = db.cursor()
    for table in schema:
        for stmt in to_sql(env, table):
            cursor.execute(stmt)
    cursor.execute("INSERT into system values ('qa_version', %s)",
            str(db_version))
    cursor.execute("INSERT into system values ('qa_infotext', '')")

# Upgrades

upgrade_map = {}

# Component that deals with database setup

class QaSetup(Component):
    """Component that deals with database setup and upgrades."""

    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        """Called when a new Trac environment is created."""
        pass

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        Returns `True` if upgrade is needed, `False` otherwise."""
        return self._get_version(db) != db_version

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade, but don't commit as
        that is done by the common upgrade procedure when all plugins are done."""
        current_ver = self._get_version(db)
        if current_ver == 0:
            create_tables(self.env, db)
        else:
            while current_ver+1 <= db_version:
                upgrade_map[current_ver+1](self.env, db)
                current_ver += 1
            cursor = db.cursor()
            cursor.execute("UPDATE system SET value=%s WHERE name='qa_version'",
                    str(db_version))

    def _get_version(self, db):
        cursor = db.cursor()
        try:
            sql = "SELECT value FROM system WHERE name='qa_version'"
            self.log.debug(sql)
            cursor.execute(sql)
            for row in cursor:
                return int(row[0])
            return 0
        except:
            return 0
