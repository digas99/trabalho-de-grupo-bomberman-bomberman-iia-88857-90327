import math

blocks = [[1,1], [1,2], [1,3], [2,1], [2,3], [3,1], [3,2], [3,3], [4,1], [4,3]]

def distance_to(obj1, obj2):
    distance = math.sqrt(math.pow((obj1[0] - obj2[0]), 2) + math.pow((obj1[1] - obj2[1]), 2))

    return distance

def get_conexions(blocks):

    conexions = []

    for i in range(len(blocks)):

        for block in blocks:

            if(distance_to(block, blocks[i]) == 1):
                conexions.append((to_string(blocks[i]), to_string(block), 1))
    
    return conexions

def to_string(ls):
    s =""
    for i in ls[:-1]:
        s += str(i) + "," 
    s += str(ls[-1])

    return s

print(get_conexions(blocks))