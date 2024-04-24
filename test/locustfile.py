import json
import os
from collections import namedtuple
import random

from locust import HttpUser, task, between


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ALL_68_QUERY_IDS = ['query_5912817.json', 'query_6387284.json', 'query_6107787.json', 'query_6259991.json',
                    'query_5909705.json', 'query_6272827.json', 'query_6534398.json', 'query_6072392.json',
                    'query_5944391.json', 'query_6480985.json', 'query_5911568.json', 'query_6045138.json',
                    'query_6608708.json', 'query_5942047.json', 'query_5916134.json', 'query_6386320.json',
                    'query_5920568.json', 'query_5912820.json', 'query_5924953.json', 'query_6104788.json',
                    'query_6084007.json', 'query_6707448.json', 'query_5924377.json', 'query_5924867.json',
                    'query_6274362.json', 'query_5925662.json', 'query_5956501.json', 'query_5912801.json',
                    'query_6462713.json', 'query_6049867.json', 'query_6004933.json', 'query_5912815.json',
                    'query_6613460.json', 'query_5947674.json', 'query_6260013.json', 'query_5908480.json',
                    'query_5912814.json', 'query_6278373.json', 'query_5912818.json', 'query_6190467.json',
                    'query_5981388.json', 'query_5948361.json', 'query_6499562.json', 'query_5947222.json',
                    'query_6050807.json', 'query_6180900.json', 'query_5942775.json', 'query_6180828.json',
                    'query_6069887.json', 'query_6566839.json', 'query_6651378.json', 'query_5926327.json',
                    'query_6462489.json', 'query_5915539.json', 'query_6482612.json', 'query_6680861.json',
                    'query_6609700.json', 'query_5909943.json', 'query_5912816.json', 'query_5943977.json',
                    'query_6356405.json', 'query_6634894.json', 'query_6024715.json', 'query_5912819.json',
                    'query_5911879.json', 'query_5921291.json', 'query_6124870.json', 'query_6024677.json']
ITRB_PROD_MATCHING_QUERY_IDS = ['query_5912817.json', 'query_5909705.json', 'query_5944391.json', 'query_5942047.json',
                                'query_5920568.json', 'query_5912820.json', 'query_5924867.json', 'query_5924377.json',
                                'query_5956501.json', 'query_5912801.json', 'query_5912815.json', 'query_5908480.json',
                                'query_5912814.json', 'query_5912818.json', 'query_5981388.json', 'query_5948361.json',
                                'query_5947222.json', 'query_6050807.json', 'query_5942775.json', 'query_5926327.json',
                                'query_6609700.json', 'query_6356405.json', 'query_5912816.json', 'query_5943977.json',
                                'query_5912819.json', 'query_5911879.json', 'query_6024677.json']
ITRB_PROD_MATCHING_OK_QUERY_IDS = ["query_5908480.json", "query_5909705.json", "query_5912801.json",
                                   "query_5912818.json", "query_5920568.json", "query_5924867.json",
                                   "query_5926327.json", "query_5942047.json", "query_5942775.json",
                                   "query_5943977.json", "query_5944391.json", "query_5947222.json",
                                   "query_5948361.json", "query_5956501.json", "query_5981388.json",
                                   "query_6024677.json", "query_6050807.json", "query_6356405.json",
                                   "query_6609700.json"]


class KG2User(HttpUser):
    @task
    def run_random_query(self):
        random_query_id = random.choice(ITRB_PROD_MATCHING_OK_QUERY_IDS)
        trapi_query = load_query_json_file(f"{SCRIPT_DIR}/sample_kg2_queries_ITRBPROD/{random_query_id}")
        self.client.post("/query", data=json.dumps(trapi_query), headers={'content-type': 'application/json'})

    wait_time = between(5, 20)


def load_query_json_file(file_path: str) -> dict:
    print(f"Loading query at {file_path}..")

    # First load the JSON query from its file
    with open(file_path, "r") as query_file:
        query_obj = json.load(query_file)

        if "input_query_canonicalized" in query_obj:
            trapi_qg = query_obj["input_query_canonicalized"]["message"]["query_graph"]

            # Remove any 'exclude' property from edges, since that isn't relevant for KP queries (always False)
            # Note: This property's presence can confuse Plater..
            for edge in trapi_qg["edges"].values():
                if "exclude" in edge:
                    del edge["exclude"]
        elif "nodes" in query_obj:
            trapi_qg = query_obj
        else:
            trapi_qg = query_obj["message"]["query_graph"]

    # Force is_set values to false
    for qnode in trapi_qg["nodes"].values():
            qnode["is_set"] = False

    return {"message": {"query_graph": trapi_qg}}
