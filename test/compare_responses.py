"""
Usage: python compare_responses.py <query_name, as specified in pytest suite; e.g., 'test_1'>
"""
import argparse
import json
import os


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("query_name", help="Name/id of the query as specified in the pytest suite; e.g., 'test_1'")
    args = arg_parser.parse_args()

    # Load the Plover and Plater responses for the specified query
    responses_dir = f"{os.path.dirname(os.path.abspath(__file__))}/responses"
    with open(f"{responses_dir}/plover_{args.query_name}.json") as plover_file:
        plover_response = json.load(plover_file)
    with open(f"{responses_dir}/plater_{args.query_name}.json") as plater_file:
        plater_response = json.load(plater_file)


    plover_kg = plover_response["message"]["knowledge_graph"]
    plater_kg = plater_response["message"]["knowledge_graph"]
    plover_nodes = plover_kg["nodes"]
    plater_nodes = plater_kg["nodes"]
    plover_node_ids = set(plover_nodes)
    plater_node_ids = set(plater_nodes)

    # Analyze the overlap or lack thereof of the nodes they returned

    plater_only_nodes = plater_node_ids.difference(plover_node_ids)
    print(f"\n\nPlater returned {len(plater_only_nodes)} nodes that Plover did not:\n")
    for node_id in plater_only_nodes:
        print(f"{node_id} {plater_nodes[node_id]['categories']} {plater_nodes[node_id].get('name')} ")

    plover_only_nodes = plover_node_ids.difference(plater_node_ids)
    print(f"\n\nPlover returned {len(plover_only_nodes)} nodes that Plater did not:\n")
    for node_id in plover_only_nodes:
        print(f"{node_id} {plover_nodes[node_id]['categories']} {plover_nodes[node_id].get('name')}")

    nodes_shared = plover_node_ids.intersection(plater_node_ids)
    print(f"\n\nThey returned {len(nodes_shared)} nodes in common:\n")
    for node_id in nodes_shared:
        print(f"{node_id} {plover_nodes[node_id]['categories']} {plover_nodes[node_id].get('name')}")

    # Look at some plater-only nodes to see what edges they came from
    plater_only_node_id = plater_node_ids.pop()
    print(f"\n\nLooking at randomly selected Plater-only node {plater_only_node_id} "
          f"({plater_nodes[plater_only_node_id].get('name')}):\n")
    for edge_key, edge in plater_kg["edges"].items():
        if edge["subject"] == plater_only_node_id or edge["object"] == plater_only_node_id:
            print(f"\n\n{edge['subject']}--{edge['predicate']}--{edge['object']}\n")
            plater_subject_node = plater_nodes[edge["subject"]]
            plater_object_node = plater_nodes[edge["object"]]
            print(f"Subject is {plater_subject_node.get('name')}, {plater_subject_node['categories']}\n")
            print(f"Object is {plater_object_node.get('name')}, {plater_object_node['categories']}")

            # Find results that use this edge
            for result in plater_response["message"]["results"]:
                result_edge_ids = {edge_binding["id"] for analysis in result["analyses"]
                                   for edge_binding in analysis["edge_bindings"]["e00"]}
                if edge_key in result_edge_ids:
                    print(f"\nFound result that includes this edge:")
                    print(result)

    # Compare what descendants of the input curie(s) the tools used
    input_curies = set(plater_response['message']['query_graph']['nodes']['n00']['ids'])
    print(f"\n\nInput curies in the QG (for n00) were: {input_curies}")

    plater_n00_node_ids = {node_binding["id"]
                           for result in plater_response["message"]["results"]
                           for node_binding in result["node_bindings"]["n00"]}
    print(f"\n\nPlater returned {len(plater_n00_node_ids)} nodes to fulfill n00:")
    for n00_node_id in plater_n00_node_ids:
        plater_node = plater_nodes[n00_node_id]
        print(f"{n00_node_id} {plater_node.get('name')}")

    plover_n00_node_ids = {node_binding["id"]
                           for result in plover_response["message"]["results"]
                           for node_binding in result["node_bindings"]["n00"]}
    print(f"\n\nPlover returned {len(plover_n00_node_ids)} nodes to fulfill n00:")
    for n00_node_id in plover_n00_node_ids:
        plover_node = plover_nodes[n00_node_id]
        print(f"{n00_node_id} {plover_node.get('name')}")





if __name__ == "__main__":
    main()