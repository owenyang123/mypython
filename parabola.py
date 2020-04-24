from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt
import numpy as np
import random
l1=range(5)
l2=range(25)
x_values=[random.choice(l1),random.choice(l1),random.choice(l1),random.choice(l1),random.choice(l1)]
y_values=[random.choice(l2),random.choice(l2),random.choice(l2),random.choice(l2),random.choice(l2)]
plt.scatter(x_values,y_values,s=10)
plt.title("",fontsize=24)
plt.xlabel("",fontsize=14)
plt.ylabel("e",fontsize=14)
plt.tick_params(axis='both',which='major',labelsize=14)
plt.show()

from tabulate import _table_formats, tabulate


format_list = list(_table_formats.keys())



table = [["spam",42], ["eggs", 451], ["bacon", 0]]
headers = ["item", "qty"]

for f in format_list:
    print("\nformat: {}\n".format(f))
    print(tabulate(table, headers, tablefmt=f))

print(chr(65))