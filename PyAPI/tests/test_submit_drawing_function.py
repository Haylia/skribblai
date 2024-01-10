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
    LOCAL_DEV_URL="http://localhost:7071/submit/drawing"
    LOCAL_DEV_REGISTER="http://localhost:7071/player/register"
    PUBLIC_REGISTER_URL = "https://skribblai-ajwl1g21-2324.azurewebsites.net/player/register?code=DrcOLAi96xZ9HD0oqVw7JiqarME0TmHUauR7d0CCBBLLAzFu9ejEQg=="
    PUBLIC_URL="https://skribblai-ajwl1g21-2324.azurewebsites.net/submit/drawing?code=Wn0EL94ahQmDHf1d2WriBxNYcgYGlIbc6TV7mEvsn4DOAzFuAmfrzg=="
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
        imageSubmission = {"username": "testname6", "roundnum": "1", "image": image_base64, 'prompt':'Jim'}

    def add_player_valid(self):
        user = {"username": "testname6", "password": "thisIsATestPassword"}
        response = requests.post(self.PUBLIC_REGISTER_URL, data=json.dumps(user))

    def test_Image_Submit(self):
        self.add_player_valid()
        response = requests.post(self.TEST_URL, data=json.dumps(self.imageSubmission))
        print(response)
        self.assertEqual(200, response.status_code)
        # gets the image from the blob storage using cosmos
        query = "SELECT * FROM c"
        items = list(self.DrawingContainerProxy.query_items(query=query, enable_cross_partition_query=True))
        image_link = items[0]['image_link']
        get_image = requests.get(image_link)
        content = get_image.content
        image_data = base64.b64decode(content)
        with open('test.png', 'wb') as f:
            f.write(image_data)

    # def test_Image_Get(self):
    #     self.add_player_valid()
    #     data = json.dumps({"username": "testname6", "roundnum": "1"})
    #     response = requests.post("http://localhost:7071/get",data=data)
    #     print(response)

    # def tearDown(self) -> None:
    #     # Use the read_all_items() method of ContainerProxy to delete all items in the container
    #     for doc in self.DrawingContainerProxy.read_all_items():
    #         self.DrawingContainerProxy.delete_item(item=doc,partition_key=doc['id'])

    #     for blob in self.DrawingStorageProxy.list_blobs():
    #         self.DrawingStorageProxy.delete_blob(blob.name)