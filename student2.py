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
        deployed_bomb_counter = 0
        destroyed_walls = []
        has_deployed = False
        after_deploy = False
        destiny = None
        last_block = "0, 0"
        before_last_block = "0, 0"
        stepCount = 0
        array_keys= []
        powerup_discover = False
        level = 0
        count_powerups = 0
        powerup_picked_up = False
        current_state = 0
        


        while True:
            try:
                print(" ")
                print("BEGINNING OF LOOP!!!")
                
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server

                while str(websocket.messages) != "deque([])":
                    state = json.loads(
                        await websocket.recv()
                    )
                
                if level < state["level"]:
                    level += 1 
                    last_key = ""
                    deployed_bomb_counter = 0
                    destroyed_walls = []
                    has_deployed = False
                    after_deploy = False
                    destiny = None
                    last_block = "0, 0"
                    before_last_block = "0, 0"
                    stepCount = 0
                    array_keys= []
                    powerup_discover = False
                    has_powerup = count_powerups
                    balloom_spotted = False
                    wall_spotted = False
                    balloom_in_range = None
                    

                bomberman = state['bomberman']
                powerup = state["powerups"]

                enem = state["enemies"] #Guarda os inimigos num array
                enem_coords = [c['pos'] for c in enem] #Guarda as coordenadas de cada balloom
                
                balloom_spotted = False

                if powerup != []:
                    powerup_discover = True
                
                elif powerup == [] and powerup_discover:
                    count_powerups += 1
                    powerup_picked_up = True
                    
                if (state['walls']== [] and state['enemies'] != [] and array_keys==[]):
                
                    if bomberman != [1,1]:

                        if has_powerup:
                            if same_line(bomberman, closest_enemy(bomberman, enem_coords)) and (distance_to(bomberman, closest_enemy(bomberman, enem_coords)) < 7):
                                key = "B"
                        else:
                            if same_line(bomberman, closest_enemy(bomberman, enem_coords)) and (distance_to(bomberman, closest_enemy(bomberman, enem_coords)) < 4):
                                key = "B"

                        blocks = get_blocks(mapa, bomberman, [1,1])
                        coordinates = get_coords(blocks)
                        conexions = get_conexions(blocks)
                        connections = Connections(conexions, coordinates)
                        print(to_string(bomberman))
                        print(to_string([1,1]))
                        p = SearchProblem(connections, to_string(bomberman), to_string([1,1]))
                        t = SearchTree(p,'a*')
                        result = t.search(90)
                        array_keys = path_to_array_keys(result[0])
                    else:
                        
                        if count_powerups > 0: 
                            array_keys = ["d","d","B","a","a","s","","","","","","","w"]

                        else:
                            array_keys = ["d","d","B","a","a","s","","","","","w"]


                if powerup_discover and not powerup_picked_up:
                        blocks = get_blocks(mapa, bomberman, state["powerups"][0][0])
                        coordinates = get_coords(blocks)
                        conexions = get_conexions(blocks)
                        connections = Connections(conexions, coordinates)
                        p = SearchProblem(connections, to_string(bomberman), to_string(state["powerups"][0][0]))
                        t = SearchTree(p,'a*')
                        result = t.search(90)
                        array_keys = path_to_array_keys(result[0])
                        
                

                elif state["exit"] != [] and state["enemies"] == [] and array_keys == [] and powerup_picked_up:
                        blocks = get_blocks(mapa, bomberman, state["exit"])
                        coordinates = get_coords(blocks)
                        conexions = get_conexions(blocks)
                        connections = Connections(conexions, coordinates)
                        p = SearchProblem(connections, to_string(bomberman), to_string(state["exit"]))
                        t = SearchTree(p,'a*')
                        result = t.search(90)
                        array_keys = path_to_array_keys(result[0])

                    

                elif state['walls']!= [] or array_keys == []:   
                    # if there are destroyed walls, then don't add them to the walls we want
                    walls = [w for w in state['walls'] if w not in destroyed_walls]
                    bomberman_string = to_string(bomberman)
                    print("AfterDeploy")
                    print(after_deploy)
                    print("len(walls)")
                    print(len(walls))
                    if(len(walls) != 0):
                        if (not after_deploy):
                            destiny = closest_wall(bomberman, walls)
                            print("destiny")
                            print(destiny)
                            after_deploy = True
                        else: 
                            next_block = "1, 0"

                    blocks = get_blocks(mapa, bomberman, destiny)
                    coordinates = get_coords(blocks)
                    conexions = get_conexions(blocks)
                    connections = Connections(conexions, coordinates)
                    p = SearchProblem(connections, bomberman_string, to_string(destiny))
                    t = SearchTree(p,'a*')
                    result = t.search(90)

                    print(result)
                    print(state)

                    print("")
                    print("enemie coord: ")
                    print(enem_coords)
                    print("Closeste enemie: ")
                    print(closest_enemy(bomberman, enem_coords))
                    print ("Bomberman: ")
                    print (bomberman)
                    print ("Closest Wall: ")
                    print (closest_wall(bomberman, walls))
                    print("Path: ")
                    print(result)            

                    #para quando fica sem path
                    if(result == None):
                        next_block = before_last_block
                    else:
                        next_block = result[0][1]
                
                    before_last_block = last_block
                    last_block = next_block

                    # let bomberman be in the same position for some frames, to be protected from bomb
                    if(count_powerups>0):
                        if (deployed_bomb_counter == 10):
                            after_deploy = False
                            deployed_bomb_counter = 0
                    else:
                        if (deployed_bomb_counter == 8):
                            after_deploy = False
                            deployed_bomb_counter = 0

                    if (deployed_bomb_counter == 0):
                        key = get_key(bomberman_string, next_block)


                    #kill balloom
                    if has_powerup and enem != []:
                        if same_line(bomberman, closest_enemy(bomberman, enem_coords)) and (distance_to(bomberman, closest_enemy(bomberman, enem_coords)) < 7):
                            key = "B"
                    elif not has_powerup and enem != []:
                        if same_line(bomberman, closest_enemy(bomberman, enem_coords)) and (distance_to(bomberman, closest_enemy(bomberman, enem_coords)) < 4):
                            key = "B"

                    # check when bomberman get close to the destiny wall and deploy bomb
                    if (result != None and len(result[0]) == 2):
                        key = "B"
                        has_deployed = True

                    # run from bomb
                    if (last_key == "B" or deployed_bomb_counter == 1):
                        if(destiny != None):
                            key = away_from_wall(bomberman, destiny)
                        deployed_bomb_counter += 1
                
                    if (deployed_bomb_counter > 1):
                        # if bomberman is between stones, one block after he deploys the bomb, then go one more block on the same direction
                        print("Is between stones")
                        print(is_between_stones(mapa, bomberman))
                        if (is_between_stones(mapa, bomberman)):
                            if (deployed_bomb_counter == 2):
                                key = last_key
                            elif (deployed_bomb_counter == 3):
                                key = change_key_randomly(last_key, bomberman, destiny, walls, deployed_bomb_counter)
                            else:
                                key = ""
                        else:
                            key = change_key_randomly(last_key, bomberman, destiny, walls, deployed_bomb_counter)
                        deployed_bomb_counter += 1


                    print("counter: ")
                    print(deployed_bomb_counter)
                    last_key = key
                    print("Key:")
                    print(key)

                if array_keys != []:
                    key= array_keys.pop(0)

                stepCount+= 1        

                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                ) 
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return




def distance_to(obj1, obj2):
    distance = math.sqrt(math.pow((obj1[0] - obj2[0]), 2) + math.pow((obj1[1] - obj2[1]), 2))

    return distance

def closest_enemy(bombermanPos, enem):

    dist_min = 123456789

    for i in range(len(enem)):

        distancia = distance_to(bombermanPos, enem[i])

        if(distancia < dist_min):

            dist_min = distancia
            minEnemy = enem[i]

    return minEnemy

def closest_wall(bombermanPos, walls): #entradas sao o bomberman e array de walls

    dist_min = 123456789
    
    for i in range(len(walls)):

        distancia = distance_to(bombermanPos, walls[i])

        if(distancia < dist_min): #verifica se a distancia é menor que a anterior

            dist_min = distancia #atualiza a distancia minima
            minWall = walls[i] #guarda o objeto parede em minWall

    return minWall

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

def away_from_wall(bomberman, wall):
    if (bomberman[0] < wall[0]):
        return "a"

    if (bomberman[0] > wall[0]):
        return "d"

    if (bomberman[1] < wall[1]):
        return "w"

    if (bomberman[1] > wall[1]):
        return "s"

def change_key_randomly(key, bomberman, destiny, walls, counter):
    print("Bomberman in rand_key:")
    print(bomberman)
    print("Destiny in rand_key:")
    print(destiny)
    # se o bomberman estiver no canto superior do mapa
    if (bomberman[1] == 1):
        # tem uma wall na mesma linha
        if (bomberman[1] == destiny[1] or counter == 4):
            return "s"

    # se o bomberman estiver no canto inferior do mapa
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
    
    print("Key:")
    print(key)
    print("Oppos_key: ")
    oppos_key = opposite_key(key)
    print(oppos_key)
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

    print("Future coords:")
    print(future_coords)
    for c in future_coords:
        for w in walls:
            # a próxima posição é uma wall
            if (future_coords.get(c)[0] == w[0] and future_coords.get(c)[1] == w[1]):
                print("returned after getting wall on future coord")
                return opposite_key(c)

    print("Diff Keys")
    print(diff_keys)
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

def path_to_array_keys(path):

    array_keys = []

    for i in range(1, len(path)):

        c_block_coords = path[i-1].split(",")
        n_block_coords = path[i].split(",")
        c_block_coords = coords_to_int(c_block_coords)
        n_block_coords = coords_to_int(n_block_coords)

        # se o x atual for menor que o próximo x
        if (c_block_coords[0] < n_block_coords[0]):
            array_keys.append("d")
        
        if (c_block_coords[0] > n_block_coords[0]):
            array_keys.append("a")
        
        if (c_block_coords[1] < n_block_coords[1]):
            array_keys.append("s")
        
        if (c_block_coords[1] > n_block_coords[1]):
            array_keys.append("w")

    return array_keys

def opposite_key(key):
    if (key == "a"):
        return "d"
    if (key == "w"):
        return "s"
    if (key == "d"):
        return "a"
    if (key == "s"):
        return "w"

def in_range(entity1, entity2, range_val): #vê tudo o que está no raio range_val
    if (abs(entity1[0] - entity2[0]) <= range_val and abs(entity1[1] - entity2[1]) <= range_val):
        return True
    return False

def same_line(entity1, entity2): #ve se o bomberman e o enemy estao no mesmo eixo
    if entity1[0] == entity2[0] or entity1[1] == entity2[1]:
        return True
    return False

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))