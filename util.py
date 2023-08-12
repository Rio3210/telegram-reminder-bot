# the below is code used to create the database 

import sqlite3

connection=sqlite3.connect("my_database.db")

with open('create_database.sql',"r") as f:
    sql=f.read()
    
connection.executescript(sql)
connection.commit()
connection.close()