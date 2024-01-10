import logging
import json
import azure.functions as func
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
import datetime
import os

# with open('local.settings.json') as settings_file:
#         settings = json.load(settings_file)

BlobStorage = BlobServiceClient.from_connection_string(os.environ['BlobStorageConnectionString'])
DrawingStorageProxy = BlobStorage.get_container_client("drawings")
MyCosmos = CosmosClient.from_connection_string(os.environ['AzureCosmosDBConnectionString'])
SkribblAIDBProxy = MyCosmos.get_database_client(os.environ['Database'])
PlayerContainerProxy = SkribblAIDBProxy.get_container_client(os.environ['PlayersContainer'])
DrawingContainerProxy = SkribblAIDBProxy.get_container_client(os.environ['DrawingsContainer'])

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
    
def get_prompt(input):
    username = input.get("username")
    roundnum = input.get("roundnum")
    # SELECT c.image_link FROM c WHERE c.username = {username} AND c.round
    query = f"SELECT * FROM c WHERE c.username = '{username}' AND c.roundnum = '{roundnum}'"
    # query = "SELECT * FROM c WHERE c.username=@username AND c.roundnum = @roundnum"

    blobImage = list(DrawingContainerProxy.query_items(query, enable_cross_partition_query=True))
    prompt = blobImage[0].get('prompt')
    logging.error(prompt)
    return prompt

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    input should include:
    - the username of the player
    - filepath to the image to be submitted to the blob storage
    """
    # input = {'username': 'username', 'round': 'roundnum'}
    # images need to be in base64 in order to 
    input = req.get_json()
    logging.info('Request to submit image.')
    try:
        result = check_user(input)
        if result["result"]:
            data = get_prompt(input)
            logging.error('works')
            return func.HttpResponse(json.dumps(data), status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse(json.dumps(result), status_code=400, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)