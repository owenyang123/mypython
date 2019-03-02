class Solution:
    def count(self, s):
       if s=="" or s==None:
           return None
       list1=list(s)
       len1=len(list1)
       count=0
       for i in range(2,len(list1)-1,1):
           if list1[i-1]==" " and (list1[i-2]=="." or list1[i-2]==",") and (ord(list1[i])>=65 and ord(list1[i])<=90):
               if list1[i+1]=="." or list1[i+1]==",":
                   count=count+1
               else:
                   pass
           elif list1[i-1]==" " and (list1[i-2]=="." or list1[i-2]==",") and (ord(list1[i])<65 or ord(list1[i])>90):
               count=count+1
               print list1[i],count
           elif (ord(list1[i])>90 or ord(list1[i])<65):
                pass
           elif (ord(list1[i])<=90 or ord(list1[i])>=65):
                count =count+1
                print list1[i],count
       if ord(list1[0])>=65 and ord(list1[0])<=90:
           pass
       else:
           count=count+1
       if ord(list1[1])>=65 and ord(list1[1])<=90:
           return count+1
       return count


k=Solution()
print k.count("Akdhsk kdjsklwfjwdlk kdldsfhcldKHJKhs ckVKJ, FJWDFHK jhkjh kshakdh. khdklhd AADDA. aSDSFW Jsdsds.")




