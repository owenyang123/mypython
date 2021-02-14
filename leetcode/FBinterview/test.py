import re

email = "tony@tiremove_thisger.net"
m = re.search("remove_this", email)
print email[:m.start()] + email[m.end():]
print m.start() , m.end()
