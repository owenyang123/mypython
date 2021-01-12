import csv
with open('ND2020-10-29.csv') as csvfile:
    spamreader = csv.reader(csvfile)
    for row in spamreader:
        print row


with open('ND2020-10-29.csv') as csvfile:
    spamreader = csvfile.readlines()
    for row in spamreader:
        print row.replace("\n","").split(",")

l=[1,2,3,4,5]
print l[0:-1]

print (30000*(1-1.05**25))/(1-1.05)