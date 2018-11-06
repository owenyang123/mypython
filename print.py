#!/usr/bin/env python
#_*_ coding:utf-8 _*_
import urllib2
# import urllib
import json
# import httplib
import re
import datetime
import sys


corpid='wxfe17b2c50796d142'
corpsecret='tMDCImcw-qXrhD8etCWgLFlewAEkpNaPmPFtfRHmfbp_s4zNNVfIk9Cup54xRbY3'
get_token='https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s'%(corpid,corpsecret)

data={
    "touser":"@all",
    "msgtype":"text",
    "agentid":"0",
    "text":{

        "content":"owen hello"
                    "5678"},
}

data=json.dumps(data,ensure_ascii=False)
f=urllib2.urlopen(get_token)
s=f.read()
f.close()
j=json.loads(s)
token=j['access_token']
print token
msm_post='https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s'%token
print msm_post
f=urllib2.urlopen(msm_post,data)
content =f.read()
print f.read
f.close
