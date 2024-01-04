import unittest
import requests
import json
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError, CosmosResourceNotFoundError
from azure.cosmos import CosmosClient

class TestPlayerRegisterFunction(unittest.TestCase):
    LOCAL_DEV_URL="http://localhost:7071/player/register"
    PUBLIC_URL="https://coursework-ajwl1g21-2324.azurewebsites.net/player/register?code=HROQTPoliBxabW1XSFYY90DaJU5-KgFvAGqxA93B5LK2AzFuO6Mdpw=="
    TEST_URL = LOCAL_DEV_URL

    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['Database'])
    PlayerContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PlayersContainer'])

    def test_add_player_valid(self):
        user = {"username": "testname6", "password": "thisIsATestPassword"}
        response = requests.post(self.TEST_URL, data=json.dumps(user))
        self.assertEqual(200, response.status_code)
    
    def test_username_too_long(self):
        user = {"username": "testnameiswaytoolong2", "password": "thisIsATestPassword"}
        response = requests.post(self.TEST_URL, data=json.dumps(user))
        dict_response = response.json()
        self.assertEqual(400, response.status_code)
        self.assertEqual("Username less than 4 characters or more than 14 characters", dict_response["msg"])

    def test_password_too_short(self):
        user = {"username": "testname", "password": "this"}
        response = requests.post(self.TEST_URL, data=json.dumps(user))
        dict_response = response.json()
        self.assertEqual(400, response.status_code)
        self.assertEqual("Password less than 10 characters or more than 20 characters", dict_response["msg"])

    def test_username_already_there(self):
        user1 = {"username": "testname", "password": "thisIsATestPassword"}
        response1 = requests.post(self.TEST_URL, data=json.dumps(user1))
        dict_response1 = response1.json()
        self.assertEqual(200, response1.status_code)
        self.assertEqual("OK", dict_response1["msg"])
        query = f"""
                SELECT VALUE r.username
                FROM root r
                WHERE IS_DEFINED(r.username) AND r.username = '{user1['username']}'
                """
        usernames = list(self.PlayerContainerProxy.query_items(query=query, enable_cross_partition_query=True))
        self.assertTrue(len(usernames) == 1)
        response2 = requests.post(self.TEST_URL, data=json.dumps(user1))
        dict_response2 = response2.json()
        self.assertEqual(400, response2.status_code)
        self.assertEqual("Username already exists", dict_response2["msg"])

    def tearDown(self) -> None:
    #    Use the read_all_items() method of ContainerProxy to delete all items in the container
       for doc in self.PlayerContainerProxy.read_all_items():
          self.PlayerContainerProxy.delete_item(item=doc,partition_key=doc['id'])
        