import numpy as np
import pandas as pd
from pandas import Series,DataFrame
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.datasets import load_boston
from sklearn.linear_model import LinearRegression
boston=load_boston()
df=DataFrame(boston.data)
df.columns=boston.feature_names
df['price']=boston.target
lreg=LinearRegression()
x_m=df.drop('price',1)
y_m=df.price
lreg.fit(x_m,y_m)
print lreg.intercept_
print len(lreg.coef_)