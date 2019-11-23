def splittwo(listinput):
    # check whether it is meaningful or not
    if not listinput or len(listinput)==1:
        return False
   #get sum 
    temp_sum=sum(listinput)
    #check odd or even
    if temp_sum % 2==1:
        return False
    #O(N) try to resolve it if it is even sum
    for i in range(len(listinput)):
        if sum(listinput[0:i+1])==temp_sum/2:
            print (listinput[0:i+1],listinput[i+1:])
            return True
    return False

print splittwo([5,2,3])