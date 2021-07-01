<<<<<<< HEAD
import re
with open("piclog") as x:
    words = re.findall(r'\w+', x.read().lower())
    print(words)
=======

for i in range(1000):
    print("set protocols mpls label-switched-path "+" "+str(i)+" to 192.168.0.224")
    print("set protocols mpls label-switched-path " + " " + str(i) + " priority 5 5")
>>>>>>> 295c06d33d7a343786ddae8356e21fe094ae868a
