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

def has_submitted(input):
    username = input.get('username')
    round_number = input.get('roundnum')

    match_found = False

    for item in DrawingContainerProxy.read_all_items():
        if item['username'] == username and item['roundnum'] == round_number:
            match_found = True
            break

    if match_found:
        return {'result': False, 'msg': 'This player has already submitted a drawing!'}
    else:
        return {"result": True, "msg": "OK"}
    
def send_image(input):
    # creates a unique ID for the image to be stored as a blob in the blob storage
    time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    blob_name=f"{input['username']}-{time}.png"
    logging.error(blob_name)
    # create a blob in the container
    blob_client = DrawingStorageProxy.get_blob_client(blob_name)
    # uploads the image to the blob storage
    blob_client.upload_blob(input['image'])
    # url to get the image from the blob storage
    blob_url = blob_client.url
    # store the user and the url to the image that they draw in the cosmosDB
    data = {
        'username': input['username'], 
        'roundnum': input['roundnum'], 
        'image_link': blob_url,
        'prompt': input['prompt']
        }
    DrawingContainerProxy.create_item(data, enable_automatic_id_generation=True)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    input should include:
    - the username of the player
    - filepath to the image to be submitted to the blob storage
    """
    # input = {'username': 'username', 'round': 'roundnum', 'image': imageString}
    # images need to be in base64 in order to 
    input = req.get_json()
    logging.info('Request to submit image.')
    try:
        result = check_user(input)
        submitted = has_submitted(input)
        if result["result"]:
            logging.error(result['msg'])
            if not submitted["result"]:
                logging.error(submitted['msg'])
                return func.HttpResponse(json.dumps(submitted), status_code=400, mimetype="application/json")
            else:
                send_image(input)
                logging.error('works')
                return func.HttpResponse(json.dumps({'result': True, 'msg':'OK'}), status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse(json.dumps(result), status_code=400, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)