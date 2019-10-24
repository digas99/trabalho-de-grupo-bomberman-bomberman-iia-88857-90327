from mapa import Map

# iterates the coordenates from an initial one, to a destiny and returns a list with only coordenates without stones withing those coordenates given
def get_blocks (mapa, start, dest):
    final_list = []
    if (start[0] > dest[0]):
        final_list= iterate_coordsX(mapa, start, dest, start[0], dest[0])
    
    else:
        final_list = iterate_coordsX(mapa, start, dest, dest[0], start[0])
    
    return final_list


def iterate_coordsX (mapa, start, dest, x_maior, x_menor):
    aux = []
    for x in range(x_menor, x_maior+1):
        if (start[1] > dest[1]):
            aux.append(iterate_coordsY(mapa, x, start[1], dest[1]))
        
        else:
            aux.append(iterate_coordsY(mapa, x, dest[1], start[1]))
    
    return aux

# is_stone não está a receber os parâmetros corretos
def iterate_coordsY (mapa, x, y_maior, y_menor):
    aux = []
    for y in range(y_menor, y_maior+1):
         if (not mapa.is_stone([x, y])):
            aux.append([x, y])
    
    return aux

# returns a dictionary {coords_string:coords, ...:..., ...}
def get_coords (list_coords):
    aux_dict = {}
    for c in list_coords:
        aux_dict[to_string(c)] = c
    
    return aux_dict

# turn coordenates into a string
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