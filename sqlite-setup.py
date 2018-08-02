import sqlite3

con = sqlite3.connect('tests.db')
con.execute("CREATE TABLE tests (id INTEGER PRIMARY KEY, name char(100) NOT NULL)")
con.execute("INSERT INTO tests (name) VALUES ('iperf')")
con.execute("INSERT INTO tests (name) VALUES ('util')")
con.commit()
