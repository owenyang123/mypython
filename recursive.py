import numpy as np
import random


from collections import defaultdict


# This class represents a directed graph
# using adjacency list representation
class Graph:

    def __init__(self, vertices):
        # No. of vertices
        self.V = vertices

        # default dictionary to store graph
        self.graph = defaultdict(list)

    # function to add an edge to graph
    def addEdge(self, u, v):
        self.graph[u].append(v)

    '''A recursive function to print all paths from 'u' to 'd'. 
    visited[] keeps track of vertices in current path. 
    path[] stores actual vertices and path_index is current 
    index in path[]'''

    def printAllPathsUtil(self, u, d, visited, path):

        # Mark the current node as visited and store in path
        visited[u] = True
        path.append(u)

        # If current vertex is same as destination, then print
        # current path[]
        if u == d:
            print path
        else:
            # If current vertex is not destination
            # Recur for all the vertices adjacent to this vertex
            for i in self.graph[u]:
                if visited[i] == False:
                    self.printAllPathsUtil(i, d, visited, path)

                # Remove current vertex from path[] and mark it as unvisited
        path.pop()
        visited[u] = False

    # Prints all paths from 's' to 'd'
    def printAllPaths(self, s, d):

        # Mark all the vertices as not visited
        visited = [False] * (self.V)

        # Create an array to store paths
        path = []

        # Call the recursive helper function to print all paths
        self.printAllPathsUtil(s, d, visited, path)

    # Create a graph given in the above diagram


def neighborlist(n):
    l=[]
    for x in range(n.shape[0]*n.shape[1]-1):
        if (x+1)%5==0:
            l.append([x,-1,x+5])
        elif x>=((n.shape[0]-1)*n.shape[1]):
            l.append([x,-1,x+1])
        else:
            l.append([x, x+5, x + 1])
    return l

def graphmade(list1):
    graph={}
    for x in list1:
        if x[1]==-1:
            graph.update({x[0]:[x[2]]})
        else:
            graph.update({x[0]:[x[1],x[2]]})
    return graph
#main function#
#generate matrix#
Matrix= np.zeros((5, 5))
for x in range(5):
    for y in range(5):
        Matrix[x][y]=int(random.randrange(0, 10000))
print Matrix

n=[]
for i in range(Matrix.shape[0]*Matrix.shape[1]):
    n.append(i)
tem1=Matrix.shape[0]-1
tem2=Matrix.shape[1]-1
n.append([tem1,tem2])
nlist=neighborlist(Matrix)
graph=graphmade(nlist)

g = Graph(Matrix.shape[0]*Matrix.shape[1])

for i in graph.keys():
    for y in graph[i]:
        g.addEdge(i,y)

s = 0
d = 24
paths=g.printAllPaths(s, d)
print paths
