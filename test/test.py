import csv
import json
import os
import time
from datetime import datetime

import pytest
import requests
from typing import Dict, Union, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ASPIRIN_CURIE = "PUBCHEM.COMPOUND:2244"
TICLOPIDINE_CURIE = "PUBCHEM.COMPOUND:5472"
ACETAMINOPHEN_CURIE = "PUBCHEM.COMPOUND:1983"
PROC_CURIE = "NCBIGene:5624"
DIETHYLSTILBESTROL_CURIE = "PUBCHEM.COMPOUND:448537"
METHYLPREDNISOLONE_CURIE = "PUBCHEM.COMPOUND:23663977"
RHOBTB2_CURIE = "NCBIGene:23221"
DIABETES_CURIE = "MONDO:0005015"
DIABETES_T1_CURIE = "MONDO:0005147"
DIABETES_T2_CURIE = "MONDO:0005148"
CAUSES_INCREASE_CURIE = "GO:0051901"
INCREASED_CURIE = "GO:0051882"
PARKINSONS_CURIE = "MONDO:0005180"
BIPOLAR_CURIE = "MONDO:0004985"


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
            tsv_writer.writerow(["query_id", "date_run", "duration_client", "duration_server", "duration_db"
                                 "num_results", "num_nodes", "num_edges", "response_size"])

    # Run the query
    client_start = time.time()
    response = requests.post(f"{pytest.endpoint}/query",
                             json={"message": {"query_graph": trapi_qg}, "submitter": "amy-test"},
                             headers={'accept': 'application/json',
                                      'Cache-Control': 'no-cache'})
    client_duration = time.time() - client_start
    print(f"Request took {response.elapsed.total_seconds()} seconds")

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
    else:
        print(f"Response status code was {response.status_code}. Response was: {response.text}")
        num_nodes, num_edges, num_results, response_size = 0, 0, 0, 0
        json_response = dict()

    # Save results/data for this query run
    db_duration = None
    if querier == "plater":
        db_duration = json_response["query_duration"]["neo4j"]
    else:
        for log_message_obj in json_response.get("logs", []):
            log_message = log_message_obj["message"]
            if log_message.startswith("***ploverdbduration"):
                db_duration = float(log_message.split(":")[-1])

    row = [query_id, datetime.now(),
           client_duration, response.elapsed.total_seconds(), db_duration,
           num_results, num_nodes, num_edges, response_size]
    with open(results_file_path, "a") as results_file_append:
        tsv_appender = csv.writer(results_file_append, delimiter="\t")
        tsv_appender.writerow(row)

    return json_response


def test_itrb_prod_kg2_sample():
    print(f"Running ITRB PROD kg2 sample queries...")
    sample_dir = f"{SCRIPT_DIR}/sample_kg2_queries_ITRBPROD"
    for file_name in os.listdir(sample_dir):
        print(f"On query {file_name}")
        if file_name.startswith("query") and file_name.endswith(".json"):
            with open(f"{sample_dir}/{file_name}", "r") as query_file:
                query_obj = json.load(query_file)
                response = _run_query(query_obj["input_query_canonicalized"], query_obj["query_id"])


def test_1():
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
             "ids": [ASPIRIN_CURIE]
          },
          "n01": {
             "categories": ["biolink:Protein"]
          }
       }
    }
    response = _run_query(query, "test_1")
    assert response["message"]["results"]


def test_2():
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
             "ids": [ACETAMINOPHEN_CURIE],
             "categories": ["biolink:ChemicalEntity"]
          },
          "n01": {
          }
       }
    }
    response = _run_query(query, "test_2")
    assert response["message"]["results"]


def test_58():
    with open(f"{SCRIPT_DIR}/queries/58_curies.json", "r") as query_file:
        big_query = json.load(query_file)
    response = _run_query(big_query, "test_58")
    assert response["message"]["results"]


def test_569():
    with open(f"{SCRIPT_DIR}/queries/569_curies.json", "r") as query_file:
        big_query = json.load(query_file)
    response = _run_query(big_query, "test_569")
    assert response["message"]["results"]


def test_764():
    with open(f"{SCRIPT_DIR}/queries/764_curies.json", "r") as query_file:
        big_query = json.load(query_file)
    response = _run_query(big_query, "test_764")
    assert response["message"]["results"]


def test_867():
    with open(f"{SCRIPT_DIR}/queries/867_curies.json", "r") as query_file:
        big_query = json.load(query_file)
    response = _run_query(big_query, "test_867")
    assert response["message"]["results"]


def test_1110():
    with open(f"{SCRIPT_DIR}/queries/1110_curies.json", "r") as query_file:
        big_query = json.load(query_file)
    response = _run_query(big_query, "test_1110")
    assert response["message"]["results"]


def test_2068():
    with open(f"{SCRIPT_DIR}/queries/2068_6172036.json", "r") as query_file:
        big_query = json.load(query_file)
    response = _run_query(big_query, "test_2068")
    assert response["message"]["results"]


def test_2674():
    with open(f"{SCRIPT_DIR}/queries/2674_6174518.json", "r") as query_file:
        big_query = json.load(query_file)
    response = _run_query(big_query, "test_2674")
    assert response["message"]["results"]


def test_sec86():
    with open(f"{SCRIPT_DIR}/queries/sec86.0_6030101.json", "r") as query_file:
        big_query = json.load(query_file)
    response = _run_query(big_query, "test_sec86")
    assert response["message"]["results"]



if __name__ == "__main__":
    pytest.main(['-v', 'test.py'])
