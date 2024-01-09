import unittest
import requests
import json
import os
import base64
# from PIL import Image
from io import BytesIO
import base64
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient


class TestPlayerRegisterFunction(unittest.TestCase):
    LOCAL_DEV_URL="http://localhost:7071/prompt/get"
    LOCAL_DEV_URL_GET_IMAGE="http://localhost:7071/get/image"
    LOCAL_DEV_SUBMIT = "http://localhost:7071/submit/drawing"
    LOCAL_DEV_REGISTER="http://localhost:7071/player/register"
    PUBLIC_SUBMIT_URL = "https://skribblai-ajwl1g21-2324.azurewebsites.net/submit/drawing?code=Wn0EL94ahQmDHf1d2WriBxNYcgYGlIbc6TV7mEvsn4DOAzFuAmfrzg=="
    PUBLIC_REGISTER_URL = "https://skribblai-ajwl1g21-2324.azurewebsites.net/player/register?code=DrcOLAi96xZ9HD0oqVw7JiqarME0TmHUauR7d0CCBBLLAzFu9ejEQg=="
    PUBLIC_URL="https://skribblai-ajwl1g21-2324.azurewebsites.net/prompt/get?code=6jTJscHXEVTvBtaAc7z7ZDfBVPrkxNsSNBa11ntv8jRWAzFu4nUQ_Q=="
    TEST_URL = PUBLIC_URL

    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['Database'])
    PlayerContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PlayersContainer'])
    DrawingContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['DrawingsContainer'])
    BlobStorage = BlobServiceClient.from_connection_string(settings['Values']['BlobStorageConnectionString'])
    DrawingStorageProxy = BlobStorage.get_container_client("drawings")
    name = "tests/Jim.jpeg"
    cwd = os.getcwd()

    with open(os.path.join(cwd, name), "rb") as data:
        image = data.read()
        image_base64 = base64.b64encode(image).decode('utf-8')
        imageSubmission = {"username": "testname6", "roundnum": "1", "image": image_base64, "prompt": "lol"}

    def add_player_valid(self):
        user = {"username": "testname6", "password": "thisIsATestPassword"}
        response = requests.post(self.PUBLIC_REGISTER_URL, data=json.dumps(user))
    
    def add_image(self):
        self.add_player_valid()
        response = requests.post(self.PUBLIC_SUBMIT_URL, data=json.dumps(self.imageSubmission))

    def test_get_prompt(self):
        self.add_image()
        # gets the image from the blob storage using cosmos
        data = {"username":'testname6', "roundnum": 1}
        response = requests.get(self.PUBLIC_URL,data=json.dumps(data))
        prompt = response.json()
        print(prompt)

    # def tearDown(self) -> None:
    #     # Use the read_all_items() method of ContainerProxy to delete all items in the container
    #     for doc in self.DrawingContainerProxy.read_all_items():
    #         self.DrawingContainerProxy.delete_item(item=doc,partition_key=doc['id'])

    #     for blob in self.DrawingStorageProxy.list_blobs():
    #         self.DrawingStorageProxy.delete_blob(blob.name)