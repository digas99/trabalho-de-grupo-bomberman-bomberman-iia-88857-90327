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
        destiny_wall = None
        last_block = "0, 0"
        before_last_block = "0, 0"
        stepCount = 0
        array_keys= []
        powerup_discovered = False
        level = 0
        wall_spotted = False
        values = {}
        wall_spotted = False
        balloom_spotted = False
        oneal_within_range = False
        current_state = -1


        while True:
            try:
                print("")
                print("BEGINNING OF LOOP")

                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server

                while str(websocket.messages) != "deque([])":
                    state = json.loads(
                        await websocket.recv()
                    )

                wall_spotted = False
                balloom_spotted = False
                oneal_within_range = False

                current_level = state['level']

                bomberman = state['bomberman']
                powerup = state["powerups"]
                
                print("POWERUPS:")
                print(powerup)

                enemies = state['enemies']

                if (current_level == 2):
                    # fetching only Oneals
                    enem_oneal = [enemy for enemy in enemies if enemy['name'] == "Oneal"]
                    #fetching coords of oneals
                    enem_oneal_coords = [c['pos'] for c in enem_oneal]

                enem_bal = [enemy for enemy in enemies if enemy['name'] == "Balloom"]
                enem_bal_coords = [c['pos'] for c in enem_bal]

                # if there are destroyed walls, then don't add them to the walls we want
                walls = state['walls']
                bomberman_string = to_string(bomberman)
                

                if(len(walls) != 0):
                    if (not after_deploy):
                        destiny_wall = closest_entity(bomberman, walls)
                        # after_deploy = True
                    else: 
                        next_block = "1, 0"

                if (len(enem_oneal) > 0):
                    destiny = closest_entity(bomberman, enem_oneal_coords)
                # se já não houverem mais oneals, foca nas walls até encontrar os powerups todos    
                else:
                    bombsCoords = powerupCoords(powerup, 'Bombs')
                    # se ainda não tiver encontrado o powerup Bombs 
                    if (bombsCoords == None):
                        destiny = destiny_wall
                    else:
                        destiny = bombsCoords
                        # verificar se o bomberman apanhou o powerup bombs
                        if (sameCoords(bomberman, bombsCoords)):
                            destiny = closest_entity(bomberman, enem_bal_coords)

                blocks = get_blocks(mapa, bomberman, destiny)
                coordinates = get_coords(blocks)
                conexions = get_conexions(blocks)

                connections = Connections(conexions, coordinates)

                p = SearchProblem(connections, bomberman_string, to_string(destiny))
                t = SearchTree(p,'a*')

                result = t.search(90)

                print("")
                print ("Bomberman: ")
                print (bomberman)

                print("Path: ")
                print(result)            

                # para quando fica sem path
                if(result == None):
                    next_block = before_last_block
                else:
                    next_block = result[0][1]
            
                before_last_block = last_block
                last_block = next_block
                
                next_block_strings_arr = next_block.split(",")
                next_block_arr = [int(s) for s in next_block_strings_arr]
            
                # if has discovered the exit, then go for it
                if (len(state["exit"]) > 0 and len(enemies) == 0):
                   next_block = to_string(state["exit"])

                # CHECK FOR WALLS ON THE WAY
                if (is_wall(walls, next_block_arr)):
                    oneal_within_range = False
                    balloom_spotted = False
                    wall_spotted = True

                # CHECK IF ONEAL IS WITHING RANGE
                for oneal in enem_oneal_coords:
                    if (in_range(bomberman, oneal, 2)):
                        oneal_within_range = True
                        balloom_spotted = False
                        wall_spotted = False
                
                # CHECK IF BALLOOM IN WITHIN RANGE
                balloom_in_range = None
                for balloom in enem_bal_coords:
                    if (in_range(bomberman, balloom, 2)):
                        balloom_in_range = balloom
                        balloom_spotted = True
                        oneal_within_range = False
                        wall_spotted = False

                if (deployed_bomb_counter == 0):
                    key = get_key(bomberman_string, next_block)

        
                if (oneal_within_range or balloom_spotted or wall_spotted):
                    key = "B"
                    has_deployed = True
                
                if (after_deploy == False):
                    if (oneal_within_range):
                        current_state = 0
                    elif (balloom_spotted):
                        current_state = 1
                    elif (wall_spotted):
                        current_state = 2

                # BOMB DEPLOYMENT---------------------------------------------------------------------

                if (key == "B" or after_deploy):
                    print("KEY IS B")
                    print("DEPLOY BOMB COUNTER: %d" % deployed_bomb_counter)
                    print("AFTER DEPLOY: %s" % after_deploy)
                    if (current_state == 0):
                        print("DEPLOYING OVER ONEAL")
                        print(destiny)
                        values = deploy_bomb(powerup, deployed_bomb_counter, last_key, mapa, bomberman, destiny, walls, key, after_deploy)
                    elif (current_state == 1):
                        print("DEPLOYING OVER BALLOOM")
                        print(balloom_in_range)
                        if (balloom_in_range != None):
                            values = deploy_bomb(powerup, deployed_bomb_counter, last_key, mapa, bomberman, balloom_in_range, walls, key, after_deploy)
                        else:
                            balloom_in_range = False
                            wall_spotted = True
                    elif (current_state == 2):
                        print("DEPLOYING OVER WALL")
                        print(destiny_wall)
                        values = deploy_bomb(powerup, deployed_bomb_counter, last_key, mapa, bomberman, destiny_wall, walls, key, after_deploy)

                    key = values["key"]
                    deployed_bomb_counter = values["dbc"]
                    after_deploy = values["ad"]

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

def away_from_wall(bomberman, wall):
    print("Bomberman in away_from_wall")
    print(bomberman)
    print("Wall in away_from_wall")
    print(wall)
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

def is_wall(walls, coords):
    for wall in walls:
        if (sameCoords(wall, coords)):
            return True
    return False

def in_range(entity1, entity2, range_val):
    if (abs(entity1[0] - entity2[0]) <= range_val and abs(entity1[1] - entity2[1]) <= range_val):
        return True
    return False

def deploy_bomb(powerup, deployed_bomb_counter, last_key, mapa, bomberman, destiny, walls, key, after_deploy):
    after_deploy = True
    # let bomberman be in the same position for some frames, to be protected form bomb
    if(powerupCoords(powerup, 'Flames') != None): 
        if (deployed_bomb_counter == 10):
            after_deploy = False
            deployed_bomb_counter = 0
    else:
        if (deployed_bomb_counter == 8):
            after_deploy = False
            deployed_bomb_counter = 0

    # run from bomb
    print("DEPLOYED BOMB COUNTER INSIDE DEPLOY BOMB")
    print(deployed_bomb_counter)
    if (last_key == "B" or deployed_bomb_counter == 1):
        print("HEREEEE")
        if (destiny != None):
            # check if bomberman is between walls
            fakeWall = is_between_walls(walls, bomberman)
            if (fakeWall == None):
                key = away_from_wall(bomberman, destiny)
            else:
                # faz um away_from_wall personalizado
                print("Size of fakeWall array")
                print(fakeWall)
                if (len(fakeWall) == 1):
                    key = away_from_wall(bomberman, fakeWall)
                else:
                    key = away_from_wall(bomberman, fakeWall[random.randint(0,1)])
        deployed_bomb_counter += 1

    if (deployed_bomb_counter > 1):
        # if bomberman is between stones, one block after he deploys the bomb, then go one more block on the same direction
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
    
    print("")
    print("RETURN OF DEPLOY BOMB")
    print("DEPLOY BOMB COUNTER: %d" % deployed_bomb_counter)
    print("AFTER DEPLOY: %s" % after_deploy)
    return {"key":key, "ad":after_deploy, "dbc":deployed_bomb_counter}

def powerupCoords(powerups, name):
    for p in powerups:
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
            return [bombX, bombY-1]
        elif (is_wall(walls, [bombX, bombY+1])):
            return [bombX, bombY+1]
        else:
            return [[bombX, bombY-1], [bombX, bombY+1]]
    
    # check the up and down coords
    if (is_wall(walls, [bombX, bombY-1]) and is_wall(walls, [bombX, bombY+1])):
        if (is_wall(walls, [bombX-1, bombY])):
            return [bombX-1, bombY]
        elif (is_wall(walls, [bombX+1, bombY])):
            return [bombX+1, bombY]
        else:
            return [[bombX-1, bombY], [bombX+1, bombY]]
    
    return None

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))