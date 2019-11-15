import MySQLdb

db = MySQLdb.connect(host="10.85.209.89",    # your host, usually localhost
                     user="owenyang",         # your username
                     passwd="222121",  # your password
                     db="stock")        # name of the data base

# you must create a Cursor object. It will let
#  you execute all the queries you need
cur = db.cursor()

# Use all the SQL you like
cur.execute("SELECT user FROM user")

# print all the first cell of all the rows
for row in cur.fetchall():
    print row[0]

db.close()