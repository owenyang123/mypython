
import smtplib
import timeit

mail_host="https://mail.sohu.com"
mail_user="66988"
mail_pass="4501"
 
 
sender = '66988@sohu.com'
receivers = ['owenyang15@gmail.com']
 
message = 'Python test.'

 
subject = 'Python SMTP test'

 
 

smtpObj = smtplib.SMTP()
smtpObj.connect(mail_host, 25)    #
smtpObj.login(mail_user,mail_pass)
smtpObj.sendmail(sender, receivers, message)
print "done"
