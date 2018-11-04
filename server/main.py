#!/usr/bin/env python3

import asyncio
import aiohttp
from aiohttp import web
import logging
import json
from datastructures.models import Teams
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from datastructures.game import Game

GAME_LOOP_INTERVAL_IN_SECONDS = 3
GAME_GRID_SIZE = 10

logging.basicConfig(level=logging.INFO)
game = Game(GAME_GRID_SIZE)

engine = engine = create_engine('postgresql://postgres:q1w2e3@localhost/WEC.db') 
Session = sessionmaker(bind=engine)
session = Session() # session to use in functions which need it

def vaidate_team(team_id, token):
    """ Returns True if the team is who they claim to be, False if not. """
    global session
    team = session.query(Teams).filter_by(team_id=team_id).first()
    if team == None: # i.e. the provided team id does not exist in the db
        return False
    return team.team_key == token

# HTTP endpoint to start game (i.e. sets game_started as true)
async def start_game(request):
    global game
    if game.started == False:
        game.start()
        logging.info("Starting game")
        data = {"Result" : "Game started"}
    else:
        data = {"Result" : "Game not started.  Game is already running."}
    return web.json_response(data)

async def stop_game(request):
    global game
    if game.started == True:
        game.stop()
        logging.info("Stopping game")
        data = {"Result" : "Game stopped"}
        # TODO: reset everything - close conns, reset game state, etc.
    else:
        data = {"Result" : "Game not stopped.  Game is not running."}
    return web.json_response(data)

# one handler spawned per websocket /connect request
async def wshandler(request):
    app = request.app
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    app["sockets"].append(ws)

    # If game is in progress, close connection (do not accept new conns)
    if game.started == True:
        await ws.send_str("Game in progress, connection rejected")
        app["sockets"].remove(ws)
        logging.debug("Closing connection since game is already in progress")
        return ws

    while 1:
        msg = await ws.receive()
        logging.debug(msg)
        if msg.type == aiohttp.WSMsgType.TEXT:
            logging.debug("Received message %s" % msg.data)
            serialized_data = json.loads(msg.data)
            
            if not vaidate_team(serialized_data["team_id"], serialized_data["token"]): # check if team is who they say they are
                logging.info("Team id and/or token invalid")
                await ws.send_str("The team id and/or token you provided is invalid.")
                break
            logging.debug("Team number %s validated" % serialized_data["team_id"])
            
            handle_request(serialized_data)
            # TODO: Ideally, we send back some sort of response confirming appropriate handling of the request or
            # return some sort of message that indicates a malformed request
            await ws.send_str("Echo: {}".format(msg.data))
        elif msg.type == aiohttp.WSMsgType.CLOSE or\
            msg.type == aiohttp.WSMsgType.ERROR:
                break

    app["sockets"].remove(ws)
    logging.debug("Closed connection.")
    return ws

# TODO: handle player moves (assess validity, etc.) if game has started

def handle_request(msg):
    messageDict = json.loads(msg)
    if "type" in messageDict and "message" in messageDict and "authenticationKey" in messageDict:
        if messageDict["type"] == "Registration":
            pass
        elif messageDict["type"] == "Move":
            pass
        else :
            logging.info("Message with invalid type received: " + msg)
    else:
        logging.info("Malformed message received: " + msg)
        return

def get_json_serialized_game_state():
    global game
    if game.current_game.is_complete == True:
        return("Team " +str(game.current_game.victor) + " won the match")
    return json.dumps(game.game_grid)

# This game loop will run infinitely and will periodically send back a JSON string summarizing game state if game is
# active
async def game_loop(app):
    global game
    while 1:
        for ws in app["sockets"]:
                        
            logging.info('Sending game state')
            await ws.send_str(get_json_serialized_game_state())
            
        # TODO: if game is over, persist results somewhere then reset game
        for ws in app["sockets"]:
            logging.info("Sending game state")
            await ws.send_str(get_json_serialized_game_state())
        await asyncio.sleep(GAME_LOOP_INTERVAL_IN_SECONDS)

app = web.Application()

# a list of all the active socket connections
app["sockets"] = []

# a dictionary of id - move queue pairs
move_queue_dict = {}

asyncio.ensure_future(game_loop(app))

# TODO: Routes should be authenticated somehow
app.router.add_route("GET", "/connect", wshandler)
app.router.add_route("GET", "/startGame", start_game)
app.router.add_route("GET", "/stopGame", stop_game)


web.run_app(app)