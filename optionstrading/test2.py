'''
question 1
Write a program that reads the text file cleanList.in, which is a list of integers separated by spaces. Remove repeated numbers and sort the numbers from greatest to least. Output into a text file cleanList.out with the same format as the input file.

Sample Input(cleanList.in):
5 4 5 2 2 8 9 1 3 6

Sample Output(cleanList.out):

9 8 6 5 4 3 2 1


'''
def fileint(inputfile):
    str_temp=""
    with open(inputfile,'r') as reader:
        temp=reader.readlines()
    for i in temp:
        str_temp+=i
    res1=sorted(list(set(str_temp.split(" "))))[::-1]
    res=" ".join(res1)
    with open('cleanList.out','w') as fd:
        fd.write(res+"\n")
    return

fileint('cleanList.in')


'''
In an alien county, each school bus is named with a bus name and each student is also assigned to a group with a group name. When a bus stops at a station to pick up students, only the students who have a group name that satisfies the rules below can get on the bus.

Both the name of the group and the name of the bus are converted into a number in the following manner: the final number is just the product of all the letters in the name, where "A" is 1 and "Z" is 26. For instance, the group "USACO" would be 21 * 19 * 1 * 3 * 15 = 17955. If the group's number mod 47 is the same as the bus's number mod 47, it is a match, then you need to tell the group to get ready! (Remember that "a mod b" is the remainder left over after dividing a by b; 34 mod 10 is 4.)

Write a program which reads in the name of the bus and the name of the group and figures out whether according to the above scheme the names are a match, printing "GO" if they match and "STAY" if not. The names of the groups and the buses will be a string of capital letters with no spaces or punctuation, up to 6 characters long.

'''
def helper(s):
    l=[]
    for i in s.upper():
        l.append(int(ord(i)))
    return reduce((lambda a,b:a*b),l)

def goorstay(bus,student):
    if not bus or not student:return "STAY"
    temp1=helper(bus)
    temp2=helper(student)
    if temp1%47==temp2%47:return "GO"
    return "STAY"
#EXAMPLE
print goorstay("COMETQ","HVNGAT")

'''
question 3
One of the farming chores Farmer John dislikes the most is hauling around lots of cow manure. In order to streamline this process, he comes up with a brilliant invention: the manure teleporter! Instead of hauling manure between two points in a cart behind his tractor, he can use the manure teleporter to instantly transport manure from one location to another.
Farmer John's farm is built along a single long straight road, so any location on his farm can be described simply using its position along this road (effectively a point on the number line). A teleporter is described by two numbers x and y, where manure brought to location x can be instantly transported to location y, or vice versa.
Farmer John wants to transport manure from location a to location b and he has built a teleporter that might be helpful during this process (of course, he doesn't need to use the teleporter if it doesn't help). Please help him determine the minimum amount of total distance he needs to haul the manure using his tractor.

'''
#get list
with open('teleport.in') as fd:
    temp=fd.readline().split(" ")
distance=sorted([int(i) for i in temp])

#get distance cost
def helper(l):
    if not helper:return 0
    temp=0
    for i in range(len(l)-1):
        temp+=l[i+1]-l[i]
    return temp
#x,y
def getxy(distance):
    if not distance or len(distance)==1:return 0
    l=[]
    for i in range(len(distance)):
        temp1=helper(distance[0:i])
        temp2=helper(distance[i:])
        l.append(temp1+temp2)
    return str(min(l))

#writefile to teleport.out
with open('teleport.out','w') as fd:
    fd.write(getxy(distance)+"\n")


