import argparse
import json
import os

import jsonlines as jsonlines

SCRIPT_DIR = f"{os.path.dirname(os.path.abspath(__file__))}"


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("kg2c_lite_filename", help="Name of the KG2c lite JSON file you want to use")
    args = arg_parser.parse_args()

    with open(f"{SCRIPT_DIR}/{args.kg2c_lite_filename}") as kg2c_lite_file:
        print(f"Starting to open KG2c lite JSON file..")
        kg2c_lite = json.load(kg2c_lite_file)

        print(f"Transforming node properties for Plater..")
        for node in kg2c_lite["nodes"]:
            node["category"] = node["all_categories"]
            del node["all_categories"]

        # Convert nodes to json lines
        print(f"Dumping nodes to json lines file..")
        with jsonlines.open(f"{SCRIPT_DIR}/kg2c-nodes.jsonl", mode="w") as jsonl_writer:
            jsonl_writer.write_all(kg2c_lite["nodes"])

        # Convert edges to json lines
        print(f"Dumping edges to json lines file..")
        with jsonlines.open(f"{SCRIPT_DIR}/kg2c-edges.jsonl", mode="w") as jsonl_writer:
            jsonl_writer.write_all(kg2c_lite["edges"])

        print(f"Done.")


if __name__ == "__main__":
    main()
