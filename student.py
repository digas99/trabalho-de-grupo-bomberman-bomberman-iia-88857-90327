import sys
import json
import asyncio
import websockets
import getpass
import os
import math
import random

from mapa import Map
from tree_search import *
from functions_d import get_blocks
from functions_d import get_coords
from functions_d import to_string
from getConexions import get_conexions
from connections import *

async def agent_loop(server_address="localhost:8000", agent_name="student"):


    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])
        
        last_key = ""
        last_key_not_B = ""
        deployed_bomb_counter = 0
        destroyed_walls = []
        has_deployed = False
        after_deploy = False
        destiny_wall = None
        last_block = "0, 0"
        before_last_block = "0, 0"
        stepCount = 0
        array_keys= ["d","d","B","a","a","s","","","","","","","w"]
        powerup_discovered = {"Flames":False, "Bombs":False, "Detonator":False, "Speed":False}
        powerup_pickedup = {"Flames":False, "Bombs":False, "Detonator":False, "Speed":False}
        level = 0
        wall_spotted = False
        values = {}
        balloom_spotted = False
        oneal_within_range = False
        doll_within_range = False
        current_state = -1
        corner_killing = False
        key_none_resolving_flag = True
        count = 0
        countStuckInCorner = 0
        bomberman = []
        previous_bomberman_pos = []
        closest_oneal = []
        previous_closest_oneal = [0,0]
        count_oneal_in_same_axis = 0
        lives = 3
        bomberman_first_position = [0,0]
        is_stuck_flag = False
        is_max_count_in_stuck = False

        while True:
            try:

                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server

                while str(websocket.messages) != "deque([])":
                    state = json.loads(
                        await websocket.recv()
                    )

                curr_lives = state["lives"]

                if lives > curr_lives:
                    lives = curr_lives
                    after_deploy = False
                    wall_spotted = False
                    oneal_within_range = False
                    doll_within_range = False
                    balloom_in_range = False
                    count = 0
                    deployed_bomb_counter = 0
                    has_deployed = False
                    values = {}

                #save the position where bomberman started the game
                if stepCount == 0:
                    bomberman_first_position = state["bomberman"]

                wall_spotted = False
                balloom_spotted = False
                oneal_within_range = False
                doll_within_range = False
                is_max_count_in_stuck = False
                
                bomberman = state['bomberman']      

                current_level = state['level']

                powerup = state["powerups"]

                enemies = state['enemies']

                # fetching only Oneals
                enem_oneal = [enemy for enemy in enemies if enemy['name'] == "Oneal"]
                #fetching coords of oneals
                if (enem_oneal != None):
                    enem_oneal_coords = [c['pos'] for c in enem_oneal]

                # fetching only Dolls
                enem_doll = [enemy for enemy in enemies if enemy['name'] == 'Doll']
                #fetching coords of Dolls
                if (enem_doll != None):
                    enem_doll_coords = [c['pos'] for c in enem_doll]

                # fetching only Ballooms
                enem_bal = [enemy for enemy in enemies if enemy['name'] == "Balloom"]
                #fetching coords of Ballooms
                if (enem_bal != None):
                    enem_bal_coords = [c['pos'] for c in enem_bal]
                
                if (len(array_keys) == 0 and len(enem_bal) > 0):
                    array_keys= ["d","d","B","a","a","s","","","","","","","w"]
                    if (powerup_pickedup["Detonator"]):
                        array_keys= ["d","d","B","a","a","s","A","w"]

                # if there are destroyed walls, then don't add them to the walls we want
                walls = state['walls']
                bomberman_string = to_string(bomberman)

            
                if(len(walls) != 0):
                    if (not after_deploy):
                        destiny = closest_entity(bomberman, walls)
                        # after_deploy = True
                    else: 
                        next_block = "1, 0"


                # if the array of powerups has some powerup in it
                if (powerup != []):
                    # then, if it wasn't pickedup, do it
                    for p in powerup:
                        powerup_coords = get_powerup_coords(powerup, p[1], powerup_discovered, powerup_pickedup)
                        if (powerup_coords != None):
                            destiny = powerup_coords["next_block"]
                            powerup_discovered[p[1]] = powerup_coords["discovered"]
                            powerup_pickedup[p[1]] = powerup_coords["pickedup"]
                            if powerup_pickedup["Detonator"]:
                                after_deploy = False

                # if has discovered the exit, then go for it
                # REMOVE LEN(WALLS), IT IS JUST FOR TESTING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                if (len(state["exit"]) > 0 and len(enemies) == 0 and powerup_pickedup["Flames"] and len(walls) == 0):
                    destiny = state["exit"]


                if (len(walls) == 0 and len(enem_bal) > 0):
                    destiny = [1,1]
                    if (bomberman == [1,1]):
                        corner_killing = True

                if (not corner_killing):

                    if (destiny == bomberman or destiny == None):
                        if (len(walls) != 0):
                            destiny = closest_entity(bomberman, walls)
                        else:
                            if (len(enem_bal_coords) != 0):
                                destiny = closest_entity(bomberman, enem_bal_coords)
                            else:
                                if (enem_oneal_coords != None and len(enem_oneal_coords) != 0):
                                    destiny = closest_entity(bomberman, enem_oneal_coords)
                                else:
                                    if (enem_doll_coords != None and len(enem_doll_coords) != 0):
                                        destiny = closest_entity(bomberman, enem_doll_coords)
                                    else:
                                        destiny = state["exit"]
                    blocks = get_blocks(mapa, bomberman, destiny)
                    coordinates = get_coords(blocks)
                    conexions = get_conexions(blocks)

                    connections = Connections(conexions, coordinates)

                    p = SearchProblem(connections, bomberman_string, to_string(destiny))
                    
                    if distance_to(bomberman, destiny) > 15:
                        t = SearchTree(p,'greedy')
                    else:
                        t = SearchTree(p,'a*')

                    result = t.search(90)            

                    # para quando fica sem path
                    if(result == None):
                        next_block = before_last_block
                    else:
                        next_block = result[0][1]
            
                    before_last_block = last_block
                    last_block = next_block
                    
                    next_block_strings_arr = next_block.split(",")
                    next_block_arr = [int(s) for s in next_block_strings_arr]
                
                #Check if bomberman is stuck 
                if(bomberman == previous_bomberman_pos):   
                    count = count + 1 

                if (count > 30):
                    is_stuck_flag = True
                    if (mapa.is_stone([bomberman[0]+0, bomberman[1]+1]) and mapa.is_stone([bomberman[0]+0, bomberman[1]-1])):
                        key = "B"
                        after_deploy = True
                        is_max_count_in_stuck = True
                        count = 0

                    elif (mapa.is_stone([bomberman[0]+1, bomberman[1]+0]) and mapa.is_stone([bomberman[0]-1, bomberman[1]+0])):
                        key = "B"
                        after_deploy = True
                        is_max_count_in_stuck = True
                        count = 0

                    else :
                        key = "B"
                        after_deploy = True
                        is_max_count_in_stuck = True
                        count = 0
                    
                if bomberman != previous_bomberman_pos:
                    count = 0

                previous_bomberman_pos = bomberman 

                # CHECK FOR WALLS ON THE WAY
                if (is_wall(walls, next_block_arr)):
                    doll_within_range = False
                    oneal_within_range = False
                    balloom_spotted = False
                    wall_spotted = True

                # CHECK IF ONEAL IS WITHING RANGE 

                for oneal in enem_oneal_coords:
                    if (in_range(bomberman, oneal, 2)):
                        doll_within_range = False
                        oneal_within_range = True
                        balloom_spotted = False
                        wall_spotted = False

                for doll in enem_doll_coords:
                    if (in_range(bomberman, doll, 2)):
                        doll_within_range = True
                        oneal_within_range = False
                        balloom_spotted = False
                        wall_spotted = False


                if (len(enem_oneal) > 0 and len(walls) == 0):
                    closest_oneal = closest_entity(bomberman, enem_oneal_coords)
                    destiny = closest_oneal
                
                if (len(enem_doll) > 0 and len(walls) == 0):
                    closest_doll = closest_entity(bomberman, enem_doll_coords)
                    destiny = closest_doll
                
                
                # CHECK IF BALLOOM IN WITHIN RANGE 
                balloom_in_range = None

                if enem_bal != []:
                    balloom_in_range = closest_entity(bomberman, enem_bal_coords)

                    if powerup_pickedup["Flames"]:
                        if same_line(bomberman, balloom_in_range) and (distance_to(bomberman, balloom_in_range) < 5):
                            doll_within_range = False
                            oneal_within_range = False
                            balloom_spotted = True
                            wall_spotted = False
                    elif not powerup_pickedup["Flames"]:
                        if same_line(bomberman, balloom_in_range) and (distance_to(bomberman, balloom_in_range) < 4):
                            doll_within_range = False
                            oneal_within_range = False
                            balloom_spotted = True
                            wall_spotted = False
                
                

                if (deployed_bomb_counter == 0 and not is_max_count_in_stuck):
                    key = get_key(bomberman_string, next_block)

        
                if (oneal_within_range or balloom_spotted or wall_spotted or doll_within_range):
                    key = "B"
                    has_deployed = True
                
                if (after_deploy == False):
                    if (oneal_within_range):
                        current_state = 0
                    elif (balloom_spotted):
                       current_state = 1
                    elif (wall_spotted):
                        current_state = 2
                    elif (doll_within_range):
                        current_state = 3

                # BOMB DEPLOYMENT---------------------------------------------------------------------
                if (is_max_count_in_stuck):
                    key = "B"
                    is_max_count_in_stuck = False

                if (key == "B" or after_deploy):
                
                    if (current_state == 0):
                        values = deploy_bomb(powerup, deployed_bomb_counter, last_key, last_key_not_B, mapa, bomberman, destiny, walls, key, after_deploy, powerup_pickedup, is_stuck_flag)
                    
                    elif (current_state == 1):
                       if (balloom_in_range != None):
                           values = deploy_bomb(powerup, deployed_bomb_counter, last_key, last_key_not_B, mapa, bomberman, balloom_in_range, walls, key, after_deploy, powerup_pickedup, is_stuck_flag)
                       else:
                           # balloom_in_range = False
                           # wall_spotted = True
                           current_state = 2

                    elif (current_state == 3):
                        values = deploy_bomb(powerup, deployed_bomb_counter, last_key, last_key_not_B, mapa, bomberman, destiny, walls, key, after_deploy, powerup_pickedup, is_stuck_flag)
                     
                    elif (current_state == 2):
                        if balloom_in_radius(bomberman, enem_bal_coords, 3) and not after_deploy and not is_stuck_flag:
                            key = ""

                        elif not balloom_in_radius(bomberman, enem_bal_coords, 3):
                            values = deploy_bomb(powerup, deployed_bomb_counter, last_key, last_key_not_B, mapa, bomberman, destiny, walls, key, after_deploy, powerup_pickedup, is_stuck_flag)
                    
                    if len(values) != 0:
                        key = values["key"]
                        deployed_bomb_counter = values["dbc"]
                        after_deploy = values["ad"]

                    last_key = key
                    if (key != "B" and key != ""):
                        last_key_not_B = key

                if (corner_killing and len(array_keys) > 0):
                    key = array_keys.pop(0)


                if (len(enem_bal) == 0):
                    corner_killing = False
                    if (key_none_resolving_flag):
                        key = ""
                        key_none_resolving_flag = False
     

                #if bomberman is stucked in the corner, after he dies
                if bomberman == bomberman_first_position:
                    countStuckInCorner = countStuckInCorner + 1
                    
                    if countStuckInCorner > 10:
                        key = "s"
                
                if bomberman != bomberman_first_position:
                    countStuckInCorner = 0

                stepCount += 1

                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                ) 
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return




def distance_to(obj1, obj2):
    distance = math.sqrt(math.pow((obj1[0] - obj2[0]), 2) + math.pow((obj1[1] - obj2[1]), 2))

    return distance


def closest_entity(bombermanPos, entities): #entradas sao o bomberman e array de walls

    dist_min = 123456789
    
    for i in range(len(entities)):

        distancia = distance_to(bombermanPos, entities[i])

        if(distancia < dist_min): #verifica se a distancia é menor que a anterior

            dist_min = distancia #atualiza a distancia minima
            minEnt = entities[i] #guarda o objeto parede em minWall

    return minEnt

def get_key(current_block, next_block):
    c_block_coords = current_block.split(",")
    n_block_coords = next_block.split(",")
    c_block_coords = coords_to_int(c_block_coords)
    n_block_coords = coords_to_int(n_block_coords)

    # se o x atual for menor que o próximo x
    if (c_block_coords[0] < n_block_coords[0]):
        return "d"
    
    if (c_block_coords[0] > n_block_coords[0]):
        return "a"
    
    if (c_block_coords[1] < n_block_coords[1]):
        return "s"
    
    if (c_block_coords[1] > n_block_coords[1]):
        return "w"

def away_from_wall(bomberman, wall, walls, last_key_not_B):

    pos_left_bomberman = get_pos_from_entity(bomberman,"left",1)
    pos_right_bomberman = get_pos_from_entity(bomberman,"right",1)
    pos_top_bomberman = get_pos_from_entity(bomberman,"top",1)
    pos_bottom_bomberman = get_pos_from_entity(bomberman,"bottom",1)
    keys1 = ["a", "d"]
    keys2 = ["w", "s"]

    # se o bomberman estiver no topo do mapa
    if (bomberman[1] == 1):
        if (wall[1] == 2):
            if (is_wall(walls, pos_left_bomberman)):
                return "d"
            elif (is_wall(walls, pos_right_bomberman)):
                return "a"
            else:
                return keys1[random.randint(0,1)]

    # se o bomberman estiver no bottom do mapa
    if (bomberman[1] == 29):
        if (wall[1] == 28):
            if (is_wall(walls, pos_left_bomberman)):
                return "d"
            elif (is_wall(walls, pos_right_bomberman)):
                return "a"
            else:
                return keys1[random.randint(0,1)]

    # se o bomberman estiver no canto esquerdo do mapa
    if (bomberman[0] == 1):
        if (wall[0] == 2):
            if (is_wall(walls, pos_top_bomberman)):
                return "s"
            elif (is_wall(walls, pos_bottom_bomberman)):
                return "w"
            else:
                return keys2[random.randint(0,1)]

    # se o bomberman estiver no canto direito do mapa
    if (bomberman[0] == 49):
        if (wall[0] == 48):
            if (is_wall(walls, pos_top_bomberman)):
                return "s"
            elif (is_wall(walls, pos_bottom_bomberman)):
                return "w"
            else:
                return keys2[random.randint(0,1)]

    # if there is a wall two blocks away from bomberman, then just go back
    if ((is_wall_in_line_of_3(walls, get_pos_from_entity(bomberman,"left",2), "vertical") and is_wall(walls, pos_right_bomberman)) or (is_wall_in_line_of_3(walls, get_pos_from_entity(bomberman,"top",2), "horizontal") and is_wall(walls, pos_bottom_bomberman)) or (is_wall_in_line_of_3(walls, get_pos_from_entity(bomberman,"right",2), "vertical") and is_wall(walls, pos_left_bomberman)) or (is_wall_in_line_of_3(walls, get_pos_from_entity(bomberman,"bottom",2), "horizontal") and is_wall(walls, pos_top_bomberman))):
        # it has to be the last_key_not_B, because the last_key will be always "B" in this situations
        return last_key_not_B
    
    if ((is_wall_with_range(walls, get_pos_from_entity(bomberman,"left",2)) and is_wall(walls, pos_right_bomberman)) or (is_wall_with_range(walls, get_pos_from_entity(bomberman,"top",2)) and is_wall(walls, pos_bottom_bomberman)) or (is_wall_with_range(walls, get_pos_from_entity(bomberman,"right",2)) and is_wall(walls, pos_left_bomberman)) or (is_wall_with_range(walls, get_pos_from_entity(bomberman,"bottom",2)) and is_wall(walls, pos_top_bomberman))):
        return opposite_key(last_key_not_B)

    if (bomberman[0] < wall[0]):
        return "a"

    if (bomberman[0] > wall[0]):
        return "d"

    if (bomberman[1] < wall[1]):
        return "w"

    if (bomberman[1] > wall[1]):
        return "s"

def change_key_randomly(key, bomberman, destiny, walls, counter):

    # se o bomberman estiver no topo do mapa
    if (bomberman[1] == 1):
        # tem uma wall na mesma linha
        if (bomberman[1] == destiny[1] or counter == 4):
            return "s"

    # se o bomberman estiver no bottom do mapa
    if (bomberman[1] == 29):
        if (bomberman[1] == destiny[1] or counter == 4):
            return "w"

    # se o bomberman estiver no canto esquerdo do mapa
    if (bomberman[0] == 1):
        if (bomberman[0] == destiny[0] or counter == 4):
            return "d"

    # se o bomberman estiver no canto direito do mapa
    if (bomberman[0] == 49):
        if (bomberman[0] == destiny[0] or counter == 4):
            return "a"

    oppos_key = opposite_key(key)
    diff_keys = [k for k in "wasd" if (k != key and k != oppos_key)]

    future_coords = {}
    # get destiny coords from diff_keys
    for d in diff_keys:
        if (d == "w"):
            future_coords['w'] = [bomberman[0], bomberman[1]-1]
        
        if (d == "a"):
            future_coords['a'] = [bomberman[0]-1, bomberman[1]]

        if (d == "s"):
            future_coords['s'] = [bomberman[0], bomberman[1]+1]
        
        if (d == "d"):
            future_coords['d'] = [bomberman[0]+1, bomberman[1]]

    for c in future_coords:
        for w in walls:
            # a próxima posição é uma wall
            if (future_coords.get(c)[0] == w[0] and future_coords.get(c)[1] == w[1]):
                return opposite_key(c)

    return diff_keys[random.randint(0,1)]

def is_between_stones(mapa, coords):
    # has stones on both sides of x axis
    if (mapa.is_stone([coords[0]-1, coords[1]]) and mapa.is_stone([coords[0]+1, coords[1]])):
        return True
    #has stones on both sides of y axis
    if (mapa.is_stone([coords[0], coords[1]-1]) and mapa.is_stone([coords[0], coords[1]+1])):
        return True
    return False
    
def coords_to_int(coords):
    return [int(coords[0]), int(coords[1])]

def string_to_arr(s):
    return [c for c in s.split(",")]

def opposite_key(key):
    if (key == "a"):
        return "d"
    if (key == "w"):
        return "s"
    if (key == "d"):
        return "a"
    if (key == "s"):
        return "w"

def is_wall(walls, coords):
    for wall in walls:
        if (sameCoords(wall, coords)):
            return True
    return False

def in_range(entity1, entity2, range_val):
    if (abs(entity1[0] - entity2[0]) <= range_val and abs(entity1[1] - entity2[1]) <= range_val):
        return True
    return False


def deploy_bomb(powerup, deployed_bomb_counter, last_key, last_key_not_B, mapa, bomberman, destiny, walls, key, after_deploy, pickedup, is_stuck_flag):
    after_deploy = True
    # let bomberman be in the same position for some frames, to be protected form bomb
    if(pickedup["Flames"]): 
        if (deployed_bomb_counter == 11):
            after_deploy = False
            deployed_bomb_counter = 0
    else:
        if (deployed_bomb_counter == 9):
            after_deploy = False
            deployed_bomb_counter = 0
    
    # run from bomb
    
    if (last_key == "B" or deployed_bomb_counter == 1):
        
        if (destiny != None):
            # check if bomberman is between walls
            fakeWall = is_between_walls(walls, bomberman)
            if (fakeWall == None):
                
                key = away_from_wall(bomberman, destiny, walls, last_key_not_B)
            else:
                # faz um away_from_wall personalizado
               
                if (len(fakeWall) == 1):
                    
                    key = away_from_wall(bomberman, fakeWall[0], walls, last_key_not_B)
                else:
                    
                    key = away_from_wall(bomberman, fakeWall[random.randint(0,1)], walls, last_key_not_B)
        deployed_bomb_counter += 1

    if (deployed_bomb_counter > 1):
        # if bomberman is between stones, one block after he deploys the bomb, then go one more block on the same direction
        if (is_between_stones(mapa, bomberman)):
            if (deployed_bomb_counter == 2):
                
                key = last_key
            elif (deployed_bomb_counter == 3):
                if (is_wall(walls, destiny)):
                   
                    key = last_key
                else:
                    
                    key = change_key_randomly(last_key, bomberman, destiny, walls, deployed_bomb_counter)
            else:
                
                key = ""
        else:
            
            key = change_key_randomly(last_key, bomberman, destiny, walls, deployed_bomb_counter)
        deployed_bomb_counter += 1
    
    # ACTIVATE DETONATOR
    # if bomberman has DETONATOR and he is still (meaning he is waiting for the bomb to explode, away from its range)
    if (deployed_bomb_counter > 3):
        if (pickedup["Detonator"] and last_key == ""):
            deployed_bomb_counter = 0
            key = "A"

    return {"key":key, "ad":after_deploy, "dbc":deployed_bomb_counter}

def entityCoords(arr_entities, name):
    for p in arr_entities:
        if (p[1] == name):
            return p[0]
    return None

def sameCoords(a, b):
    return a[0] == b[0] and a[1] == b[1]

# função retorna a(s) coord(s) que não é/são wall(s) 
def is_between_walls(walls, bomberman):
    bombX = bomberman[0]
    bombY = bomberman[1]

    # check the left and right coords
    if (is_wall(walls, [bombX-1, bombY]) and is_wall(walls, [bombX+1, bombY])):
        if (is_wall(walls, [bombX, bombY-1])):
            return [[bombX, bombY-1]]
        elif (is_wall(walls, [bombX, bombY+1])):
            return [[bombX, bombY+1]]
        else:
            return [[bombX, bombY-1], [bombX, bombY+1]]
    
    # check the up and down coords
    if (is_wall(walls, [bombX, bombY-1]) and is_wall(walls, [bombX, bombY+1])):
        if (is_wall(walls, [bombX-1, bombY])):
            return [[bombX-1, bombY]]
        elif (is_wall(walls, [bombX+1, bombY])):
            return [[bombX+1, bombY]]
        else:
            return [[bombX-1, bombY], [bombX+1, bombY]]
    
    return None

def check_powerup_discovered(array, nome):
    if (entityCoords(array, nome) != None):
        return True
    return False

def check_powerup_pickedup(inArray, discovered):
    if (discovered and inArray == None):
        return True
    return False

def get_powerup_coords(array, name, discovered, pickedup):
    # check if Flames was discovered, only if it is False
    if (not discovered[name]):
        discovered[name] = check_powerup_discovered(array, name)

    # check if Flames was pickedup
    pickedup[name] = check_powerup_pickedup(entityCoords(array, name), discovered[name])

    # if Flames was discovered but not pickedup yet, then next_block is the coords of Flames
    if (discovered[name] and not pickedup[name]):
        next_block = entityCoords(array, name)

    return {"next_block":next_block, "discovered":discovered, "pickedup":pickedup}

def center_of_path(path, rounding):
    if (rounding == "ceil"):
        return path[math.ceil(len(path)/2)]
    elif (rounding == "floor"):
        return path[math.floor(len(path)/2)]
    else:
        return None

def get_pos_from_entity(entity, side, range_val):
    if (side == "left"):
        return [entity[0]-range_val, entity[1]]
    elif(side == "right"):
        return [entity[0]+range_val, entity[1]]
    elif(side == "top"):
        return [entity[0], entity[1]-range_val]
    elif(side == "bottom"):
        return [entity[0], entity[1]+range_val]
    else:
        return None

def is_wall_in_line_of_3(walls, coords, direction):
    if (is_wall(walls, coords)):
        return True
    
    # if the line to be checked is horizontal
    if (direction == "horizontal"):
        # check the left position of the line of three
        if(is_wall(walls,get_pos_from_entity(coords, "left", 1))):
            return True

        # check the right position of the line of three
        if(is_wall(walls,get_pos_from_entity(coords, "right", 1))):
            return True
    
    # same as above, but with different directions
    if (direction == "vertical"):
        if(is_wall(walls,get_pos_from_entity(coords, "top", 1))):
            return True
        if(is_wall(walls,get_pos_from_entity(coords, "bottom", 1))):
            return True
    
    return False

def is_wall_with_range(walls, coords):
    if (is_wall(walls, coords)):
        return True
    return False
    
#check if bomberman and enemie are on the same axis
def same_line(entity1, entity2): 
    if entity1[0] == entity2[0] or entity1[1] == entity2[1]:
        return True
    return False

#check if balloom is in radius
def balloom_in_radius(bomberman, enem_coords, range): #bomberman, enem_bal_coords

    for balloom in enem_coords:

        if distance_to(bomberman, balloom) < range:
            return True 

    return False

def mid_range_point(entity1, entity2):
    return [math.ceil((entity1[0] + entity2[0])/2), math.ceil((entity1[1] + entity2[1])/2)]


#check the distance from closest balloom to bomberman
#def distance_to_closest_balloom(bomberman, balloom_in_range, range_val):
#    if same_line(bomberman, balloom_in_range) and (distance_to(bomberman, balloom_in_range) < range_val):
#        return True
#    return False

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))