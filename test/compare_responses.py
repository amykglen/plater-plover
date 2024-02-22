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
        print(f"{node_id} {plater_nodes[node_id]['categories']} {plater_nodes[node_id]['name']} ")

    plover_only_nodes = plover_node_ids.difference(plater_node_ids)
    print(f"\n\nPlover returned {len(plover_only_nodes)} nodes that Plater did not:\n")
    for node_id in plover_only_nodes:
        print(f"{node_id} {plover_nodes[node_id]['categories']} {plover_nodes[node_id]['name']}")

    nodes_shared = plover_node_ids.intersection(plater_node_ids)
    print(f"\n\nThey returned {len(nodes_shared)} nodes in common:\n")
    for node_id in nodes_shared:
        print(f"{node_id} {plover_nodes[node_id]['categories']} {plover_nodes[node_id]['name']}")

    # Look at some plater-only nodes to see what edges they came from
    plater_only_node_id = plater_node_ids.pop()
    print(f"\n\nLooking at randomly selected Plater-only node {plater_only_node_id} "
          f"({plater_nodes[plater_only_node_id]['name']}):\n")
    for edge_key, edge in plater_kg["edges"].items():
        if edge["subject"] == plater_only_node_id or edge["object"] == plater_only_node_id:
            print(f"\n\n{edge['subject']}--{edge['predicate']}--{edge['object']}\n")
            plater_subject_node = plater_nodes[edge["subject"]]
            plater_object_node = plater_nodes[edge["object"]]
            print(f"Subject is {plater_subject_node['name']}, {plater_subject_node['categories']}\n")
            print(f"Object is {plater_object_node['name']}, {plater_object_node['categories']}")

            # Find results that use this edge
            for result in plater_response["message"]["results"]:
                result_edge_ids = {edge_binding["id"] for analysis in result["analyses"]
                                   for edge_binding in analysis["edge_bindings"]["e00"]}
                if edge_key in result_edge_ids:
                    print(f"\nFound result that includes this edge:")
                    print(result)


    # Look at subclass_of edges in both responses
    plover_subclass_of_edges = [edge for edge in plover_kg["edges"].values() if edge["predicate"] == "biolink:subclass_of"]
    plater_subclass_of_edges = [edge for edge in plater_kg["edges"].values() if edge["predicate"] == "biolink:subclass_of"]
    print(f"\n\nPlover KG includes {len(plover_subclass_of_edges)} subclass_of edges")
    print(f"Plater KG includes {len(plater_subclass_of_edges)} subclass_of edges")





if __name__ == "__main__":
    main()