import sys
import json
import asyncio
import websockets
import getpass
import os
import math

from mapa import Map


async def agent_loop(server_address="localhost:8000", agent_name="student"):


    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])
        
        

        while True:
            try:
                
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server

                key = "s"
                
                walls = state["walls"] #array de walls

                bomberman_pos = state["bomberman"] ##guarda a posicao do bomberman

                closestWall = closest_wall(bomberman_pos, walls)

                p = astar(mapa.map, bomberman_pos, closestWall)
                print(p)

                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                ) 
                break
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return


class Node():
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position
    
#f = g + h
#f -> custo total do nó
#g -> distancia do nó atual ao inicio
#h -> heuristic: distancia do nó atual ao objetivo(end)

def astar(mapa,start,end):

    start_node = Node(None, start)
    start_node.g = 0
    start_node.h = 0
    start_node.f = 0

    end_node = Node(None, end)
    end_node.g = 0
    end_node.h = 0
    end_node.f = 0

    open_list = []
    close_list = []

    open_list.append(start_node) #adiciona o primeiro no à lista

    while len(open_list) > 0: #continua a procurar ate encontrar o end_node

        #obtem o nó atual
        current_node = open_list[0]
        current_index = 0

        for index, item in enumerate(open_list): #acede a todos os elementos da lista
            if item.f < current_node.f:
                current_node = item
                current_index = index
        
        open_list.pop(current_index) #o nó atual sai da open_list
        close_list.append(current_node) #e vai pra close_list 
                                        
        
        if current_node == end_node:
            path = [] #inicializa o path
            current = current_node
            while current is not None:
                path.append(current.position) #adiciona o current ao path
                current = current.parent
            return path[::-1] #retorna um path invertido

        children = [] #lista de nos filhos

        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]: #quadrados

            node_position = (current_node.position[0]+new_position[0], current_node.position[1]+new_position[1])

            if node_position[0] > (len(mapa) - 1) or node_position[0] < 0 or node_position[1] > (len(mapa[len(mapa)-1]) -1) or node_position[1] < 0:
                continue #garante que está dentro do limite

            if mapa[node_position[0]][node_position[1]] != 0:
                continue #garante q está numa zona onde pode passar

            new_node = Node(current_node, node_position)

            children.append(new_node) #adiciona a novo nó à lista de filhos
        
        for child in children:

            for close_child in close_list:
                if child == close_child:
                    continue
            
            child.g = current_node.g+1
            child.h = ((child.position[0] - end_node.position[0])**2) + ((child.position[1] - end_node.position[1])**2)
            child.f = child.g + child.h

            for open_node in open_list: #child esta na openlist
                if child == open_node and child.g > open_node.g:
                    continue
            
            open_list.append(child) #acrescenta o no filho à openlist

def distance_to(obj1, obj2):
    return math.sqrt(((obj1[0]-obj2[0])**2)+((obj1[1]-obj2[1])**2))

def closest_wall(bombermanPos, walls): #entradas sao o bomberman e array de walls

    dist_min = 123456789
    
    for i in walls:

        if(distance_to(bombermanPos, walls[i]) < dist_min): #verifica se a distancia é menor que a anterior

            dist_min = distance_to(bombermanPos, walls[i]) #atualiza a distancia minima
            minWall = walls[i] #guarda o objeto parede em minWall

    return minWall








# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))