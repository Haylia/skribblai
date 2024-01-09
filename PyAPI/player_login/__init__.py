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

def login_player(input_data):
    username = input_data.get("username")
    password = input_data.get("password")

    match_found = False

    for item in PlayerContainerProxy.read_all_items():
        if item["username"] == username and item["password"] == password:
            match_found = True
            break

    if match_found:
        return {"result": True, "msg": "OK"}
    else:
        return {"result": False, "msg": "Username or password incorrect"}
   
def main(req: func.HttpRequest) -> func.HttpResponse:
    input = req.get_json()
    logging.info('Request to log in a player.')
    try:
        
        result = login_player(input)
        if result["result"]:
            return func.HttpResponse(json.dumps(result), status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse(json.dumps(result), status_code=400, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)