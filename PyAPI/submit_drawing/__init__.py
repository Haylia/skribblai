import logging
import json
import azure.functions as func
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient

with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
BlobStorage = BlobServiceClient.from_connection_string(settings['Values']['BlobStorageConnectionString'])
DrawingsStorageProxy = BlobStorage.get_container_client("drawings")
SkribblAIDBProxy = MyCosmos.get_database_client(settings['Values']['Database'])
PlayerContainerProxy = SkribblAIDBProxy.get_container_client(settings['Values']['PlayersContainer'])
DrawingContainerProxy = SkribblAIDBProxy.get_container_client(settings['Values']['DrawingsContainer'])

def check_user(input):
    # Checking if the user exists in the CosmosDB player container
    username = input.get("username")

    match_found = False

    for item in PlayerContainerProxy.read_all_items():
        if item["username"] == username:
            match_found = True
            break

    if match_found:
        return {"result": True, "msg": "OK"}
    else:
        return {"result": False, "msg": "Username is not in database"}
    
def send_image(input):
    # uploads the image to the blob storage account
    pass

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    input should include:
    - the username of the player
    - filepath to the image to be submitted to the blob storage
    """
    input = req.get_json()
    logging.info('Request to submit image.')
    try:
        result = check_user(input)
        if result["result"]:
            return func.HttpResponse(json.dumps(result), status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse(json.dumps(result), status_code=400, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)