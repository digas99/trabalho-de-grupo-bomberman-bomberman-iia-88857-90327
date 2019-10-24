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
        
        last_key = "d"
        deployed_bomb_counter = 0

        while True:
            try:
                
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server

                bomberman = state['bomberman']
                walls = state['walls']
                bomberman_string = to_string(bomberman)
                
                destiny_wall = closest_wall(bomberman, walls)


                blocks = get_blocks(mapa, bomberman, destiny_wall)
                coordinates = get_coords(blocks)
                connections = get_conexions(blocks)

                print ("Bomberman: ")
                print (bomberman)
                print ("Closest Wall: ")
                print (closest_wall(bomberman, walls))
                print ("Coords: ")
                print (coordinates)
                print ("Connec: ")
                print (connections)
                
                connections = Connections(connections, coordinates)
    
                p = SearchProblem(connections, bomberman_string, to_string(destiny_wall))
                t = SearchTree(p,'a*')

                result = t.search(90)
                print(result, t.length, t.ramification)

                next_block = result[0][1]
                
                # check when bomberman get close to the destiny wall and deploy bomb
                if (len(result[0]) == 2):
                    key = "B"
                else:
                    key = get_key(bomberman_string, next_block)

                # run from bomb
                if (last_key == "B"):
                    key = away_from_wall(bomberman, destiny_wall)
                    deployed_bomb_counter += 1

                if (deployed_bomb_counter > 0):
                    if (deployed_bomb_counter == 1):
                        key = last_key
                        deployed_bomb_counter += 1
                    else:
                        key = change_key_randomly(last_key)

                last_key = key

                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                ) 
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return




def distance_to(obj1, obj2):
    distance = math.sqrt(math.pow((obj1[0] - obj2[0]), 2) + math.pow((obj1[1] - obj2[1]), 2))

    return distance


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
    print (c_block_coords)
    print (n_block_coords)

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

def change_key_randomly(key):
    diff_keys = []
    for k in "wasd":
        if (k != key):
            diff_keys.append(k)
    
    print(diff_keys)
    return diff_keys[random.randint(0,2)]
    

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))