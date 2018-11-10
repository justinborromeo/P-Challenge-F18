# WEC Fall 18 Programming Challenge
## Overview
Competitors are tasked with developing bots to play the Tron lightbike game against other teams' bots.  The server in this repo handles the competition and accepts messages (via Websockets) from bots indicating registration and direction of movement.

## Setup
The server is written in Python (specifically, Python 3) and requires the following pip packages:
- websockets
- asyncio
- psycopg2
- aiohttp
- sqlalchemy
The project also uses PostgreSQL.  Once installed, create a database called WEC.db with a user named postgres and the password q1w2e3.  Alternatively, these credentials can be changed in the connection string in main.py.  On first execution of main.py, the ORM will auto create the tables.

## Adding Team Credentials
Run add_team_to_db.py.  It will prompt you for a team_id.  Once given an id, it will add the team to the database then return a authentication key.
