import unittest
import requests
import json
import os
import base64
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient

class TestPlayerRegisterFunction(unittest.TestCase):
    LOCAL_DEV_URL="http://localhost:7071/submit/drawing"
    LOCAL_DEV_REGISTER="http://localhost:7071/player/register"
    PUBLIC_URL="https://coursework-ajwl1g21-2324.azurewebsites.net/player/register?code=HROQTPoliBxabW1XSFYY90DaJU5-KgFvAGqxA93B5LK2AzFuO6Mdpw=="
    TEST_URL = LOCAL_DEV_URL

    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['Database'])
    PlayerContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PlayersContainer'])
    name = "tests/Jim.jpeg"
    cwd = os.getcwd()

    with open(os.path.join(cwd, name), "rb") as data:
        image = data.read()
        image_base64 = base64.b64encode(image).decode('utf-8')
        imageSubmission = {"username": "testname6", "roundnum": "1", "image": image_base64}

    def add_player_valid(self):
        user = {"username": "testname6", "password": "thisIsATestPassword"}
        response = requests.post(self.LOCAL_DEV_REGISTER, data=json.dumps(user))

    def test_Image_Submit(self):
        self.add_player_valid()
        response = requests.post(self.TEST_URL, data=json.dumps(self.imageSubmission))
        print(response)
        self.assertEqual(200, response.status_code)