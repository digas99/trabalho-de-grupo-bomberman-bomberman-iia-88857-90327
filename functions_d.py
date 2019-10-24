from mapa import Map

def get_blocks (start, dest):
    final_array = []
    if (start[0] > dest[0]):
        final_array = iterate_coordsX(start, dest, start[0], dest[0])
    
    else:
        final_array = iterate_coordsX(start, dest, dest[0], start[0])
    
    return final_array


def iterate_coordsX (start, dest, x_maior, x_menor):
    aux = []
    for x in range(x_menor, x_maior+1):
        if (start[1] > dest[1]):
            aux.append(iterate_coordsY(x, start[1], dest[1]))
        
        else:
            aux.append(iterate_coordsY(x, dest[1], start[1]))
    
    return aux

# is_stone não está a receber os parâmetros corretos
def iterate_coordsY (x, y_maior, y_menor):
    aux = []
    for y in range(y_menor, y_maior+1):
         if (not Map.is_stone([x, y])):
            aux.append([x, y])
    
    return aux

def get_coords (list_coords):
    aux_dict = {}
    for c in list_coords:
        aux_dict[to_string(c)] = c
    
    return aux_dict

def to_string (coords):
    count = 0
    s = ""
    for i in coords:
        if (count == len(coords)-1):
            s += str(i)
        else:
            s += str(i) +  ","
        count+=1
    return s

print(get_coords(get_blocks([0,0], [2,3])))