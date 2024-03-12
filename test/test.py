import csv
import json
import os
import time
import traceback
from datetime import datetime

import pytest
import requests
from typing import Dict, Union, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _print_kg(kg: Dict[str, Dict[str, Dict[str, Dict[str, Union[List[str], str, None]]]]]):
    nodes_by_qg_id = kg["nodes"]
    edges_by_qg_id = kg["edges"]
    for qnode_key, node_ids in sorted(nodes_by_qg_id.items()):
        print(f"{qnode_key}: {node_ids}")
    for qedge_key, edge_ids in sorted(edges_by_qg_id.items()):
        print(f"{qedge_key}: {edge_ids}")


def _run_query(trapi_query: Dict[str, Dict[str, Dict[str, Union[List[str], str, None]]]],
               query_id: str):
    # Grab the query graph (might be nested under 'message')
    trapi_qg = trapi_query if "nodes" in trapi_query else trapi_query["message"]["query_graph"]

    # Get set up to store query results
    querier = "plover" if "rtxkg2" in pytest.endpoint else "plater"
    results_file_path = f"{SCRIPT_DIR}/{querier}.tsv"
    if not os.path.exists(results_file_path):
        with open(results_file_path, "w+") as results_file:
            tsv_writer = csv.writer(results_file, delimiter="\t")
            tsv_writer.writerow(["query_id", "date_run", "duration_client", "duration_server", "duration_db",
                                 "num_results", "num_nodes", "num_edges", "response_size"])

    # Run the query
    client_start = time.time()
    try:
        response = requests.post(f"{pytest.endpoint}/query",
                                 json={"message": {"query_graph": trapi_qg}, "submitter": "amy-test"},
                                 headers={'accept': 'application/json',
                                          'Cache-Control': 'no-cache'})
        client_duration = time.time() - client_start
        request_duration = response.elapsed.total_seconds()
        print(f"Request took {request_duration} seconds")

        # Process/save results
        if response.status_code == 200:
            json_response = response.json()
            num_nodes = len(json_response["message"]["knowledge_graph"]["nodes"])
            num_edges = len(json_response["message"]["knowledge_graph"]["edges"])
            num_results = len(json_response["message"]["results"])

            # Save the response locally
            os.system(f"mkdir -p {SCRIPT_DIR}/responses")
            response_path = f"{SCRIPT_DIR}/responses/{querier}_{query_id}.json"
            with open(response_path, "w+") as response_file:
                json.dump(json_response, response_file)

            # Grab the size of the response
            response_size = os.path.getsize(response_path)
            # TODO: Grab the backend database query time from the logs

            # Save results/data for this query run
            db_duration = None
            if querier == "plater":
                db_duration = json_response["query_duration"]["neo4j"]
            else:
                for log_message_obj in json_response.get("logs", []):
                    log_message = log_message_obj["message"]
                    if log_message.startswith("***ploverdbduration"):
                        db_duration = float(log_message.split(":")[-1])
        else:
            print(f"Response status code was {response.status_code}. Response was: {response.text}")
            num_nodes, num_edges, num_results, response_size, db_duration = 0, 0, 0, 0, 0
            json_response = dict()
    except Exception:
        client_duration = time.time() - client_start
        request_duration = client_duration
        db_duration = 0
        print(f"Request to KP threw an exception! Traceback: {traceback.format_exc()}")
        num_nodes, num_edges, num_results, response_size = 0, 0, 0, 0
        json_response = dict()

    row = [query_id, datetime.now(),
           client_duration, request_duration, db_duration,
           num_results, num_nodes, num_edges, response_size]
    with open(results_file_path, "a") as results_file_append:
        tsv_appender = csv.writer(results_file_append, delimiter="\t")
        tsv_appender.writerow(row)

    return json_response


def run_query_json_file(file_path: str):
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

    query_file_name = file_path.strip("/").split("/")[-1]

    response = _run_query(trapi_qg, query_id=query_file_name)


def run_directory_of_queries(dir_name: str):
    print(f"Running {dir_name} kg2 sample queries...")
    sample_dir = f"{SCRIPT_DIR}/{dir_name}"
    for file_name in sorted(list(os.listdir(sample_dir))):
        print(f"On query {file_name}")
        if file_name.startswith("query") and file_name.endswith(".json"):
            run_query_json_file(f"{sample_dir}/{file_name}")


def test_json_query():
    # Need to use the '--queryfile <path to query file>' command line option when running this test
    assert pytest.queryfile
    assert os.path.isfile(pytest.queryfile)
    run_query_json_file(pytest.queryfile)


def test_directory_of_json_queries():
    # Need to use the '--querydir <path to directory of queries>' command line option when running this test
    assert pytest.querydir
    assert os.path.isdir(pytest.querydir)
    run_directory_of_queries(pytest.querydir)


def test_simple_1():
    # Simplest one-hop
    query = {
       "edges": {
          "e00": {
             "subject": "n00",
             "object": "n01",
             "predicates": ["biolink:interacts_with"]
          }
       },
       "nodes": {
          "n00": {
             "ids": ["PUBCHEM.COMPOUND:2244"]
          },
          "n01": {
             "categories": ["biolink:Protein"]
          }
       }
    }
    response = _run_query(query, "test_1")
    assert response["message"]["results"]


def test_simple_2():
    # Output qnode is lacking a category
    query = {
       "edges": {
          "e00": {
             "subject": "n00",
             "object": "n01",
             "predicates": ["biolink:related_to"]
          }
       },
       "nodes": {
          "n00": {
             "ids": ["PUBCHEM.COMPOUND:1983"],
             "categories": ["biolink:ChemicalEntity"]
          },
          "n01": {
          }
       }
    }
    response = _run_query(query, "test_2")
    assert response["message"]["results"]


if __name__ == "__main__":
    pytest.main(['-v', 'test.py'])
