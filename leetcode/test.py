import pyodbc
conn = pyodbc.connect('Driver={SQL Server Native Client 11.0};'
                      'Server=DESKTOP-MIB48GA\oweny;'
                      'Database=MSSQLSERVER;'
                      "username = sa;"                   
                       "password = 222121wj;"
                      'Trusted_Connection=yes;')

cursor = conn.cursor()
cursor.execute('SELECT * FROM MSSQLSERVER.Table')

for row in cursor:
    print(row)

def power123(a,b):
    if a==1:
        return 1
    if b==0:
        return 1
    if b==1:
        return a
    if b<0:
        return 1.0000/float(power123(a,-b))
    if b%2==0:
        return power123(a,b/2)*power123(a,b/2)
    else:
        return power123(a, b / 2) * power123(a, b / 2)*a

