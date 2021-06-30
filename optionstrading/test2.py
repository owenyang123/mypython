from itertools import product
list1 = range(1,3)
list2 = range(4,6)
list3 = range(7,9)
for i in product(list1, list2, list3):
    print(i)
for item1,item2,item3 in product(list1, list2, list3):
    print(item1+item2+item3)