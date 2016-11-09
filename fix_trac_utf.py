#!/usr/bin/env python
import sqlite3

conn_trac = sqlite3.connect('c:/Workspace/test/db/trac.db')
conn_trac.create_function('FIXENCODING', 1, lambda s: str(s).decode('latin-1'))
conn_trac.execute(""" UPDATE qa_testcase SET title = FIXENCODING(CAST(title AS BLOB)) """)
conn_trac.commit()
conn_trac.execute(""" UPDATE qa_testcase SET steps = FIXENCODING(CAST(steps AS BLOB)) """)
conn_trac.commit()
conn_trac.execute(""" UPDATE qa_testcase SET acceptance = FIXENCODING(CAST(acceptance AS BLOB)) """)
conn_trac.commit()
conn_trac.close()

