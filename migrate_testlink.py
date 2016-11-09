#!/usr/bin/env python
import pymysql
import re
import sqlite3

p = re.compile(r'<.*?>')

def remove_tags(data):
    return p.sub('', data)

conn = pymysql.connect(host='127.0.0.1', port=3306, user='testlink',
                       passwd='testlink', db='testlink')
cur = conn.cursor()

cur.execute("""
SELECT h1.name, v.steps, v.expected_results FROM tcversions v
INNER JOIN nodes_hierarchy h ON v.id = h.id
INNER JOIN nodes_hierarchy h1 ON h.parent_id = h1.id;""")

conn_trac = sqlite3.connect('c:/Temp/trac.db')
cur_trac = conn_trac.cursor()

for r in cur.fetchall():
   cur_trac.execute("""
    INSERT INTO qa_testcase(title, steps, acceptance) VALUES(?, ?, ?);""",
                    (r[0], remove_tags(r[1]), remove_tags(r[2])))
   conn_trac.commit()

cur_trac.close()
conn_trac.close()

cur.close()
conn.close()

