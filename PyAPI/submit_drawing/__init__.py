import logging
import json
import azure.functions as func
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
import datetime

with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)

BlobStorage = BlobServiceClient.from_connection_string(settings['Values']['BlobStorageConnectionString'])
DrawingStorageProxy = BlobStorage.get_container_client("drawings")
MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
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
    # creates a unique ID for the image to be stored as a blob in the blob storage
    logging.info('TESTING')
    # blob_name=f"{input['username']}-{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    blob_name = 'test' # need to change it to something else
    logging.error(blob_name)
    logging.info('STARTING UPLOAD TO BLOB')
    # create a blob in the container
    blob_client = DrawingStorageProxy.get_blob_client(blob_name)
    # uploads the image to the blob storage
    blob_client.upload_blob(input['image'])
    logging.info('UPLOAD TO BLOB COMPLETE')
    # url to get the image from the blob storage
    blob_url = blob_client.url
    # store the user and the url to the image that they draw in the cosmosDB
    data = {
        'username': input['username'], 
        'roundnum': input['roundnum'], 
        'image_link': blob_url
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
        if result["result"]:
            send_image(input)
            logging.error('works')
            return func.HttpResponse(json.dumps({'result': True, 'msg':'OK'}), status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse(json.dumps(result), status_code=400, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)