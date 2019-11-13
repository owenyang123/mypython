import string,random
cap=""
words="".join((string.ascii_letters,string.digits))
print words
for i in range(8):
    cap+=random.choice(words)
    print cap