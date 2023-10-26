"""
This script converts the KG2c TSV files into KGX-compliant JSON lines files, ready for import into Plater.

Usage: python convert_kg2c_tsvs_to_jsonl.py <nodes TSV file path> <edges TSV file path> \
                                                <nodes header TSV file path> <edges header TSV file path>
"""
import argparse
import ast
import csv
import json
import logging
import os
import sys

import jsonlines
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARRAY_DELIMITER = "ǂ"
ARRAY_COL_NAMES = {"all_names", "all_categories", "equivalent_curies", "publications", "kg2_ids"}
KGX_COL_NAME_REMAPPINGS = {
    "all_categories": "category",
    "category": "preferred_category"
}
csv.field_size_limit(sys.maxsize)  # Required because some KG2c fields are massive

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    handlers=[logging.FileHandler("build.log"),
                              logging.StreamHandler()])


def parse_value(value: any, col_name: str):
    if col_name in ARRAY_COL_NAMES:
        if value:
            return value.split(ARRAY_DELIMITER)
        else:
            return []
    elif value in {"True", "False", "true", "false"}:
        return ast.literal_eval(value)
    else:
        return value


def convert_tsv_to_jsonl(tsv_path: str, header_tsv_path: str):
    """
    This method assumes the input TSV file names are in KG2c format (e.g., like nodes_c.tsv and nodes_c_header.tsv)
    """
    logging.info(f"\n\n**** Starting to process file {tsv_path} (header file is: {header_tsv_path}) ****")

    jsonl_output_file_path = tsv_path.replace('.tsv', '.jsonl')
    logging.info(f"Output file path will be: {jsonl_output_file_path}")

    # First load column names and remove the ':type' suffixes neo4j requires on column names
    header_df = pd.read_table(header_tsv_path)
    column_names = [col_name.split(":")[0] if not col_name.startswith(":") else col_name
                    for col_name in header_df.columns]
    node_column_indeces = {col_name: index for index, col_name in enumerate(column_names)}
    logging.info(f"Columns mapped to their indeces are:\n "
                 f"{json.dumps(node_column_indeces, indent=2)}")
    columns_to_keep = [col_name for col_name in column_names if not col_name.startswith(":")]
    logging.info(f"We'll use this subset of ({len(columns_to_keep)}) columns:\n "
                 f"{json.dumps(columns_to_keep, indent=2)}")

    logging.info(f"Starting to convert rows in {tsv_path} to json lines..")
    with open(tsv_path, "r") as input_tsv_file:

        with jsonlines.open(jsonl_output_file_path, mode="w") as jsonl_writer:

            batch = []
            num_rows_processed = 0
            tsv_reader = csv.reader(input_tsv_file, delimiter="\t")
            for line in tsv_reader:
                row_obj = dict()
                for col_name in columns_to_keep:
                    raw_value = line[node_column_indeces[col_name]]
                    if raw_value not in {"", "{}", "[]", None}:  # Only skip empty values, not false ones
                        kgx_col_name = KGX_COL_NAME_REMAPPINGS.get(col_name, col_name)
                        row_obj[kgx_col_name] = parse_value(raw_value, col_name)

                batch.append(row_obj)
                if len(batch) == 1000000:
                    jsonl_writer.write_all(batch)
                    num_rows_processed += len(batch)
                    batch = []
                    logging.info(f"Have processed {num_rows_processed} rows...")

            # Take care of writing the (potential) final partial batch
            if batch:
                jsonl_writer.write_all(batch)

    logging.info(f"Done converting rows in {tsv_path} to json lines.")


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("nodes_tsv_path", help="Path to the nodes TSV file you want to transform")
    arg_parser.add_argument("edges_tsv_path", help="Path to the edges TSV file you want to transform")
    arg_parser.add_argument("nodes_header_tsv_path", help="Path to the header TSV file for your nodes file")
    arg_parser.add_argument("edges_header_tsv_path", help="Path to the header TSV file for your edges file")
    args = arg_parser.parse_args()
    logging.info(f"Input args are:\n {args}")

    convert_tsv_to_jsonl(args.nodes_tsv_path, args.nodes_header_tsv_path)
    convert_tsv_to_jsonl(args.edges_tsv_path, args.edges_header_tsv_path)

    logging.info(f"\n\nDone converting KG2c nodes/edges TSVs to KGX JSON lines format.")


if __name__ == "__main__":
    main()
