import math
from tree_search import *
from functions_d import get_blocks
from functions_d import get_coords
from getConexions import get_conexions

class Connections(SearchDomain):
    def __init__(self,connections, coordinates):
        self.connections = connections
        self.coordinates = coordinates
    def actions(self,coord):
        actlist = []
        for (P1,C2,D) in self.connections:
            if (P1==coord):
                actlist += [(P1,C2)]
            elif (C2==coord):
               actlist += [(C2,P1)]
        return actlist 
    def result(self,coord,action):
        (P1,C2) = action
        if P1==coord:
            return C2
    def cost(self, coord, action):
        (P1,C2) = action
        if P1 != coord:
            return None == (P1,c2)
        for(P1,c2,D) in self.connections:
            if action == (P1,c2) or action == (c2,P1):
                return D;
    def heuristic(self, state, goal_state):
        #print(state)
        #print(goal_state)
        c1_x,c1_y = self.coordinates[state]
        c2_x,c2_y = self.coordinates[goal_state]

        return math.hypot(c1_x-c2_x,c1_y-c2_y)

blocks = [[7, 2], [7, 3], [7, 4], [7, 5], [8, 3], [8, 5], [9, 2], [9, 3], [9, 4], [9, 5], [10, 3], [10, 5]]
print("String coords: ")
print(get_coords(blocks))
print("String conex")
print(get_conexions(blocks))
connections = Connections(get_conexions(blocks), get_coords(blocks))
p = SearchProblem(connections,'7,2','10,5')
t = SearchTree(p,'a*')

# Atalho para obter caminho de c1 para c2 usando strategy:
def search_path(c1,c2,strategy):
    my_prob = SearchProblem(connections,c1,c2)
    my_tree = SearchTree(my_prob)
    my_tree.strategy = strategy
    return my_tree.search()

print(t.search(90), t.length, t.ramification)