import argparse
import json


def should_filter_out(edge: dict) -> bool:
    primary_ks = edge.get("primary_knowledge_source")
    publications = edge.get("publications")
    if primary_ks == "infores:semmeddb" and (not publications or len(publications) < 4):
        return True
    elif edge.get("domain_range_exclusion") in {True, "True", "true"}:
        return True
    else:
        return False


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("kg2c_lite_json_path", help="Path to the kg2c_lite_2.X.Y.json.gz file you want to transform")
    args = arg_parser.parse_args()

    with open(args.kg2c_lite_json_path, "r") as kg2c_lite_json_file:
        kg2c_lite_json = json.load(kg2c_lite_json_file)

    print(f"At start, kg2c lite json has {len(kg2c_lite_json['nodes'])} nodes and {len(kg2c_lite_json['edges'])} edges")

    # Get rid of semmeddb edges with fewer than 4 publications and domain_range_exclusion edges
    filtered_graph = {key: [] if key == "edges" else value
                      for key, value in kg2c_lite_json.items()}
    num_edges_filtered = 0
    for edge in kg2c_lite_json['edges']:
        if not should_filter_out(edge):
            filtered_graph["edges"].append(edge)
        else:
            num_edges_filtered += 1
    print(f"In the end, we filtered out {num_edges_filtered} edges.")

    print(f"The filtered kg2c lite graph has {len(filtered_graph['nodes'])} nodes and "
          f"{len(filtered_graph['edges'])} edges")

    with open(f"{args.kg2c_lite_json_path}_filtered", "w+") as filtered_json_file:
        json.dump(filtered_graph, filtered_json_file, indent=2)


if __name__ == "__main__":
    main()
