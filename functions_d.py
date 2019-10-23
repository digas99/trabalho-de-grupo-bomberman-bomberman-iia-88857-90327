stones = [[2, 2], [4, 2]]

def get_blocks (s, d):
    final_array = []
    if (s[0] > d[0]):
        final_array = iterate_coordsX(s[0], d[0])
    
    else:
        final_array = iterate_coordsX(d[0], s[0])
    
    return final_array


def iterate_coordsX (x_maior, x_menor):
    aux = []
    for x in range(x_menor, x_maior+1):
        if (s[1] > d[1]):
            aux.append(iterate_coordsY(x, s[1], d[1]))
        
        else:
            aux.append(iterate_coordsY(x, d[1], d[1]))
    
    return aux


def iterate_coordsY (x, y_maior, y_menor):
    aux = []
    for y in range(y_menor, y_maior+1):
         if (not is_stone(x, y)):
            aux.append([x, y])
    
    return aux


def is_stone(x, y):
    for s in stones:
        if (s[0] == x and s[1] == y):
            return True
    
    return False