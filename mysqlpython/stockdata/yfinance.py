import pandas as pd

data=pd.read_csv("D:\pythonproject\pythonlearning\\03- General Pandas\Pandas-Exercises\\banklist.csv")

print data.columns
print data.groupby('ST').count().sort_values('Bank Name',ascending=False).iloc[:5]
print data[data['ST']=='CA'].groupby('City').count().sort_values('Bank Name')
print data['Bank Name'].apply(lambda x:"Bank" not in x)
print sum([True,False,True])