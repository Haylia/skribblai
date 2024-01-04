import unittest
import requests
import json
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient

class TestPlayerRegisterFunction(unittest.TestCase):
    LOCAL_DEV_URL="http://localhost:7071/player/login"
    LOCAL_DEV_REGISTER="http://localhost:7071/player/register"
    PUBLIC_URL="https://coursework-ajwl1g21-2324.azurewebsites.net/player/login?code=HROQTPoliBxabW1XSFYY90DaJU5-KgFvAGqxA93B5LK2AzFuO6Mdpw=="
    PUBLIC_REGISTER_URL="https://coursework-ajwl1g21-2324.azurewebsites.net/player/register?code=HROQTPoliBxabW1XSFYY90DaJU5-KgFvAGqxA93B5LK2AzFuO6Mdpw=="
    TEST_URL = LOCAL_DEV_URL

    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['Database'])
    PlayerContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PlayersContainer'])
    
    def create_items(self):
        user = {"username": "testname", "password": "thisIsATestPassword"}
        response = requests.post(self.LOCAL_DEV_REGISTER, data=json.dumps(user))

        user2 = {"username": "testname2", "password": "Passwordtest23"}
        response = requests.post(self.LOCAL_DEV_REGISTER, data=json.dumps(user2))

    def test_login_valid(self):
        self.create_items()
        login = {"username": "testname", "password": "thisIsATestPassword"}
        response = requests.get(self.TEST_URL, data=json.dumps(login))
        dict_response = response.json()
        self.assertEqual(200, response.status_code)
        
    def test_login_username_invalid(self):
        self.create_items()
        login = {"username": "ttestname", "password": "thisIsATestPassword"}
        response = requests.get(self.TEST_URL, data=json.dumps(login))
        dict_response = response.json()
        self.assertEqual(400, response.status_code)
        self.assertEqual("Username or password incorrect", dict_response["msg"])

    def test_login_password_invalid(self):
        self.create_items()
        login = {"username": "testname", "password": "thisIsATestPassworg"}
        response = requests.get(self.TEST_URL, data=json.dumps(login))
        dict_response = response.json()
        self.assertEqual(400, response.status_code)
        self.assertEqual("Username or password incorrect", dict_response["msg"])

    def tearDown(self) -> None:
        # Use the read_all_items() method of ContainerProxy to delete all items in the container
        for doc in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=doc,partition_key=doc['id'])

        
