import re
sample1='May 29 17:[1-2]'
sample2='\'request '
sample3='\'set '
sample4='\'deactivate '
sample5='\'commit'
sample6='\'edit '
sample7='\'activate '
with open('clilog') as f:
    for i in f.readlines():
        if re.search(sample1,i):
            if re.search(sample2,i) or re.search(sample3,i) or re.search(sample4,i) or re.search(sample5,i) or re.search(sample6,i) or re.search(sample7,i):
                print(" ".join(i.split(" ")[0:3]),end=",")
                print(i.split(",")[-1])