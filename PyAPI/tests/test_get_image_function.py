import unittest
import requests
import json
import os
import base64
from PIL import Image
from io import BytesIO
import base64
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient


class TestPlayerRegisterFunction(unittest.TestCase):
    LOCAL_DEV_URL="http://localhost:7071/get/image"
    LOCAL_DEV_SUBMIT = "http://localhost:7071/submit/drawing"
    LOCAL_DEV_REGISTER="http://localhost:7071/player/register"
    PUBLIC_URL="https://coursework-ajwl1g21-2324.azurewebsites.net/player/register?code=HROQTPoliBxabW1XSFYY90DaJU5-KgFvAGqxA93B5LK2AzFuO6Mdpw=="
    TEST_URL = LOCAL_DEV_URL

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
        imageSubmission = {"username": "testname6", "roundnum": "1", "image": image_base64}

    def add_player_valid(self):
        user = {"username": "testname6", "password": "thisIsATestPassword"}
        response = requests.post(self.LOCAL_DEV_REGISTER, data=json.dumps(user))
    
    def add_image(self):
        self.add_player_valid()
        response = requests.post(self.LOCAL_DEV_SUBMIT, data=json.dumps(self.imageSubmission))

    def test_get_image(self):
        self.add_image()
        # gets the image from the blob storage using cosmos
        data = {"username":'testname6', "roundnum": 1}
        response = requests.post(self.TEST_URL,data=json.dumps(data))
        image_link = response.json()
        print(image_link)
        get_image = requests.get(image_link)
        content = get_image.content
        image_data = base64.b64decode(content)
        with open('test.png', 'wb') as f:
            f.write(image_data)
        # data = json.dumps({"username": "testname6", "roundnum": "1"})
        

    # def tearDown(self) -> None:
    #     # Use the read_all_items() method of ContainerProxy to delete all items in the container
    #     for doc in self.DrawingContainerProxy.read_all_items():
    #         self.DrawingContainerProxy.delete_item(item=doc,partition_key=doc['id'])

    #     for blob in self.DrawingStorageProxy.list_blobs():
    #         self.DrawingStorageProxy.delete_blob(blob.name)