from jnpr.junos import Device

dev = Device(host = '10.85.209.89', user='root', password='NewUser1')
dev.open()
x=dev.cli('ps-aux')
print x
dev.close()
