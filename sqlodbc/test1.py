import matplo
from numpy  import array
import matplotlib.pyplot as plt
fig = plt.figure()
ax = fig.add_subplot(111)
DataX =[1,2,3,4,5,6,7]
DataY =[7,6,5,4,3,2,1]
ax.scatter(DataX,DataY,15.0*array(DataX),15.0*array(DataY))

