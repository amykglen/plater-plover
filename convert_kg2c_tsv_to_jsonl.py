import argparse
import ast
import csv
import json
import logging
import os

import jsonlines
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARRAY_DELIMITER = "ǂ"
ARRAY_COL_NAMES = {"all_names", "all_categories", "equivalent_curies", "publications", "kg2_ids"}
KGX_COL_NAME_REMAPPINGS = {
    "all_categories": "category",
    "category": "preferred_category"
}

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    handlers=[logging.FileHandler("build.log"),
                              logging.StreamHandler()])


def download_kg2c_tsvs():
    # Only works if you have the aws CLI set up, of course
    logging.info(f"Downloading KG2pre TSV source files..")
    kg2c_tarball_name = "kg2c-tsv.tar.gz"
    logging.info(f"Downloading {kg2c_tarball_name} from the rtx-kg2 S3 bucket")
    os.system(f"aws s3 cp --no-progress --region us-west-2 s3://rtx-kg2/{kg2c_tarball_name} .")
    logging.info(f"Unpacking {kg2c_tarball_name}..")
    os.system(f"tar -xvzf {kg2c_tarball_name}")


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


def convert_tsv_to_jsonl(tsv_filename: str, header_tsv_filename: str):
    logging.info(f"**** Starting to process file {tsv_filename} (header file is: {header_tsv_filename}) ****")

    jsonl_output_file_name = tsv_filename.replace('.tsv', '.jsonl')
    logging.info(f"Output filename will be: {jsonl_output_file_name}")

    # First load column names and remove the ':type' suffixes neo4j requires on column names
    header_df = pd.read_table(f"{SCRIPT_DIR}/{header_tsv_filename}")
    column_names = [col_name.split(":")[0] if not col_name.startswith(":") else col_name
                    for col_name in header_df.columns]
    node_column_indeces = {col_name: index for index, col_name in enumerate(column_names)}
    logging.info(f"Columns mapped to their indeces are:\n "
                 f"{json.dumps(node_column_indeces, indent=2)}")
    columns_to_keep = [col_name for col_name in column_names if not col_name.startswith(":")]
    logging.info(f"We'll use this subset of ({len(columns_to_keep)}) columns:\n "
                 f"{json.dumps(columns_to_keep, indent=2)}")

    logging.info(f"Starting to convert rows in {tsv_filename} to json lines..")
    with open(f"{SCRIPT_DIR}/{tsv_filename}", "r") as input_tsv_file:

        with jsonlines.open(f"{SCRIPT_DIR}/{jsonl_output_file_name}", mode="w") as jsonl_writer:

            tsv_reader = csv.reader(input_tsv_file, delimiter="\t")
            for line in tsv_reader:
                row_obj = dict()
                for col_name in columns_to_keep:
                    raw_value = line[node_column_indeces[col_name]]
                    if raw_value not in {"", "{}", "[]", None}:  # Only skip empty values, not false ones
                        kgx_col_name = KGX_COL_NAME_REMAPPINGS.get(col_name, col_name)
                        row_obj[kgx_col_name] = parse_value(raw_value, col_name)

                jsonl_writer.write(row_obj)

    logging.info(f"Done converting rows in {tsv_filename} to json lines.")


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("nodes_tsv_filename", help="Name of the nodes TSV file you want to transform")
    arg_parser.add_argument("edges_tsv_filename", help="Name of the edges TSV file you want to transform")
    arg_parser.add_argument("nodes_header_tsv_filename", help="Name of the header TSV file for your nodes file")
    arg_parser.add_argument("edges_header_tsv_filename", help="Name of the header TSV file for your edges file")
    args = arg_parser.parse_args()
    logging.info(f"Input args are:\n {args}")

    convert_tsv_to_jsonl(args.nodes_tsv_filename, args.nodes_header_tsv_filename)
    convert_tsv_to_jsonl(args.edges_tsv_filename, args.edges_header_tsv_filename)


if __name__ == "__main__":
    main()
