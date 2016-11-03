#!/usr/bin/env python
#_*_ coding:utf-8 _*_
import urllib2
# import urllib
import json
# import httplib
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

def wechat_send(token, wechat_msg):
    data={
        "touser":"@all",
        "msgtype":"text",
        "agentid":"0",
        "text":{
            "content":wechat_msg,
        },
    }
    data=json.dumps(data,ensure_ascii=False)
    msm_post='https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s'%token
    f=urllib2.urlopen(msm_post,data)
    content =f.read()
    f.close
    print content

if __name__ == '__main__':

    inputfile = sys.argv[1]
    print inputfile

    #we get token from wechat first. It should last 7200 seconds
    corpid='wxfe17b2c50796d142'
    corpsecret='tMDCImcw-qXrhD8etCWgLFlewAEkpNaPmPFtfRHmfbp_s4zNNVfIk9Cup54xRbY3'
    get_token='https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s'%(corpid,corpsecret)
    f=urllib2.urlopen(get_token)
    print get_token
    s=f.read()
    f.close()
    j=json.loads(s)
    token=j['access_token']

    #Process alarms
    alarmfile = open(inputfile)
    msg = "P1 in ATT queue"
    for line in alarmfile:
        if re.search(r"rpd", line):
#            dt = re.search(r"(\d+-\d+-\d+ \d+:\d+:\d+)", line).group(1)
#           if getDatetimeFromStr(dt) >= previous_hour():
                msg = msg + line + "\n"
    print msg
    if len(msg) != 0:
        wechat_send(token, msg)