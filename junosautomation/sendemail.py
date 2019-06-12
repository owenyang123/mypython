import win32com.client


def sendmail(to, title, body):
    olMailItem = 0
    ol = win32com.client.Dispatch("Outlook.Application")
    msg = ol.CreateItem(olMailItem)
    msg.To = to
    msg.Subject = title
    msg.Body = body
    msg.Send()

sendmailowenyang15@gmail.com", "replication", "we saw the issue")("