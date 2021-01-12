import collections
import re,copy


l=[1,2,3,4,6]

with open("piclog") as x:
    words = re.findall(r'\w+', x.read().lower())
    print collections.Counter(words).most_common(10)


re_telephone = re.compile(r'^(\d{3})-(\d{3,8})$')
print re_telephone.match('010-12345').groups()
print re_telephone.match('010-8086').groups()
('010', '8086')

x={'sea':{'core':["abc"]}}
l1=[["sea","ce","bcd"],["sea1","core","bcd"],["sea","ce","bcd1"],["sea3","ce","bcd1"],["sea","ce","aaabcd1"]]
for i in l1:
    if i[0] in x:
        if i[1] in x[i[0]]:
            x[i[0]][i[1]].append(i[2])
        else:
            x[i[0]][i[1]]=[i[2]]
    else:
        x[i[0]]={i[1]:[i[2]]}
print x