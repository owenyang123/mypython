import MySQLdb
db = MySQLdb.connect("127.0.0.1","owenyang","222121wj","stock" )
cursor = db.cursor()
cursor.execute("SELECT VERSION()")

data = cursor.fetchone()
print ("Database version : %s " % data)


db.close()