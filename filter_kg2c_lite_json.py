import argparse
import json

import jsonlines


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("kg2c_lite_json_path", help="Path to the kg2c_lite_2.X.Y.json.gz file you want to filter")
    arg_parser.add_argument("kg2c_edges_jsonl_path", help="Path to the already-filtered KG2c jsonl edges file")
    args = arg_parser.parse_args()

    # Grab the IDs of the kept edges from the jsonl file
    with jsonlines.open(args.kg2c_edges_jsonl_path) as reader:
        jsonl_edge_ids = {int(edge_row["id"]) for edge_row in reader}
    print(f"Edges jsonl file has {len(jsonl_edge_ids)} kept edge ids")

    # Load the kg2c lite json file that we need to filter
    with open(args.kg2c_lite_json_path, "r") as kg2c_lite_json_file:
        kg2c_lite_json = json.load(kg2c_lite_json_file)
    print(f"At start, kg2c lite json has {len(kg2c_lite_json['nodes'])} nodes "
          f"and {len(kg2c_lite_json['edges'])} edges")

    # Get rid of semmeddb edges with fewer than 4 publications and domain_range_exclusion edges
    filtered_graph = {key: [] if key == "edges" else value
                      for key, value in kg2c_lite_json.items()}
    for edge in kg2c_lite_json['edges']:
        if int(edge["id"]) in jsonl_edge_ids:
            filtered_graph["edges"].append(edge)
    print(f"The filtered kg2c lite graph has {len(filtered_graph['nodes'])} nodes and "
          f"{len(filtered_graph['edges'])} edges")

    # Save the filtered kg2c lite json
    with open(f"{args.kg2c_lite_json_path}_filtered", "w+") as filtered_json_file:
        json.dump(filtered_graph, filtered_json_file, indent=2)


if __name__ == "__main__":
    main()
