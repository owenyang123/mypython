import urllib2
import urllib
import json
import httplib
import re
import datetime
import sys

def getDatetimeFromStr(s):
  format = '%Y-%m-%d %H:%M:%S'
  return datetime.datetime.strptime(s, format)

def previous_hour():
    dt = datetime.datetime.now()
    dt2 = dt.strftime('%Y-%m-%d %H')+":00:00"
    return getDatetimeFromStr(dt2)-datetime.timedelta(hours=1)
def geturl(url):
    page=urllib.urlopen(url)
    html=page.read()
    return html
def getimg(html):
    reg=r'"(*376*)"'
    imgre=re.compile(reg)
    imglist=re.findall(imgre,html)
    return imglist

k=geturl("https://japan2.usembassy.gov/e/visa/tvisa-niv-admin.html")
reg=r'.*079/376.*.'
txtre=re.compile(reg)
txtlist=re.findall(txtre,k)
k=txtlist



def wechat_send(token,msg,url1):
        data={
            "touser":"@all",
            "msgtype":"news",
            "agentid":"0",
            "news":{
                 "articles": [
             {
                 "title":msg,
                 "description":msg,
                 "url":msg,
                 #"picurl":url1,
             },
             ]
            },
        }
        data=json.dumps(data,ensure_ascii=False)
        msm_post='https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s'%token
        f=urllib2.urlopen(msm_post,data)
        content =f.read()
        f.close

if __name__ == '__main__':

#    inputfile = sys.argv[1]
#    print inputfile

    #we get token from wechat first. It should last 7200 seconds
    corpid='wxfe17b2c50796d142'
    corpsecret='tMDCImcw-qXrhD8etCWgLFlewAEkpNaPmPFtfRHmfbp_s4zNNVfIk9Cup54xRbY3'
    get_token='https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s'%(corpid,corpsecret)
    f=urllib2.urlopen(get_token)
    s=f.read()
    f.close()
    j=json.loads(s)
    token=j['access_token']
    msg = "hello"
    t=0
    for x in k:
        print x
        t=t+1
        wechat_send(token,x,x)