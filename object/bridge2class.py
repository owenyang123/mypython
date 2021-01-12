class cen:
    def __init__(self,value=36.0):
        self.value=float(value)
    def __get__(self,instance,owner):
        return self.value
    def __set__(self,instance,value):
        self.value=float(value)
class fah:
    def __get__(self,instance,owner):
        return instance.x1*1.8+32
    def __set__(self,instance,value):
        instance.x1=(float(value)-32)/1.8

class temperature:
    x2=fah()
    x1 = cen()
temp=temperature()
temp.x1=40
print(temp.x2)