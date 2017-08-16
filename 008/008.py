import urllib
import urllib2
from bs4 import BeautifulSoup

url = "http://www.juniper.net"
page = urllib2.urlopen(url)

soup = BeautifulSoup(page)
print soup.body.text