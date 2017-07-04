import random
import string
import MySQLdb

forSelect = string.ascii_letters + string.digits
def generate_code(count, length):
    sum=[]
    for x in range(count):
        Re = ""
        for y in range(length):
            Re += random.choice(forSelect)
        sum.append(Re)
    return sum
if __name__ == '__main__':
   sum=generate_code(200, 20)
   s1=len(sum)
   conn=MySQLdb.connect(host="localhost",user="root",passwd="222121wj",db="codesaving",charset="utf8")
   cursor = conn.cursor()
   for i in range(0,s1):
       code=sum[i]
       print code
       cursor.execute("insert into codedetail values (%s)", (str(code)))
   cursor.close()
   conn.close()