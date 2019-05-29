<<<<<<< HEAD
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

k=geturl("http://www9.health.gov.au/cda/source/rpt_1.cfm")
print k
reg=r'.*Hepatitis B*.'
txtre=re.compile(reg)
txtlist=re.findall(txtre,k)
k1=txtlist

k=geturl("http://www9.health.gov.au/cda/source/rpt_1.cfm")
reg=r'.*parentNode.*.'
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
    print k1,k
    for x in k1:
        print x
        t = t + 1
        wechat_send(token, x, t)
    t=0
    for x in k:
        print x
        t=t+1
=======
class Solution:
    def countAndSay(self, n):
        if n==0:
            return "1"
        if n==1:
            return "11"
        for i in range(2,n+1):
            l=self.numbercount(self.countAndSay(i-1))
        return l
    def numbercount(self,string):
        lsum=[]
        l=[]
        k=len((string))
        if k==1:
            l=[[1,string]]
            return "1"+string
        i=0
        while (i <=k - 1 ):
            if i  == k - 1:
                l.append([1,string[i]])
                break
            if string[i]==string[i+1]:
                if i+1==k-1:
                    lsum.append(string[i])
                    lsum.append(string[i+1])
                    l.append([len(lsum),lsum[0]])
                    lsum=[]
                    break
                elif string[i+1]!=string[i+2]:
                    lsum.append(string[i])
                    lsum.append(string[i + 1])
                    i=i+2
                    l.append([len(lsum),lsum[0]])
                    lsum=[]
                else:
                    lsum.append(string[i])
                    i=i+1
            else:
                l.append([1,string[i]])
                i=i+1
        str123=""
        for i in l:
            str123=str123+str(i[0])+str(i[1])
        return str123
k=Solution()
print k.countAndSay(5)
>>>>>>> d95ec67a08eaac77d3858962c1ac4580db756ad7
