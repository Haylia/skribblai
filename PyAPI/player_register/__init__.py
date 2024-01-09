import logging
import json
import os
import azure.functions as func
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError

# with open('local.settings.json') as settings_file:
#     settings = json.load(settings_file)
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
SkribblAIDBProxy = MyCosmos.get_database_client(os.environ['Database'])
DrawingContainerProxy = SkribblAIDBProxy.get_container_client(os.environ['DrawingsContainer'])
PlayerContainerProxy = SkribblAIDBProxy.get_container_client(os.environ['PlayersContainer'])


def register_player(input):
    username = input.get("username")
    password = input.get("password")

    if len(username) < 4 or len(username) > 14:
        return {"result": False, "msg": "Username less than 4 characters or more than 14 characters"}

    if len(password) < 10 or len(password) > 20:
        return {"result": False, "msg": "Password less than 10 characters or more than 20 characters"}

    for item in PlayerContainerProxy.read_all_items():
        if item.get("username") == username:
            return {"result": False, "msg": "Username already exists"}
    player = {
        "username": username,
        "password": password,
        "games_played": 0,
        "total_score": 0
    }
    PlayerContainerProxy.create_item(player,enable_automatic_id_generation=True)
    return {"result": True, "msg": "OK"}

def main(req: func.HttpRequest) -> func.HttpResponse:
    input = req.get_json()
    logging.info('Request to register a new player.')

    try:
        result = register_player(input)
        if result["result"]:
            return func.HttpResponse(json.dumps(result), status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse(json.dumps(result), status_code=400, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)
