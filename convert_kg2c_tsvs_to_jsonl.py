"""
This script converts the KG2c TSV files into KGX-compliant JSON lines files, ready for import into Plater.

Usage: python convert_kg2c_tsvs_to_jsonl.py <nodes TSV file path> <edges TSV file path> \
                                                <nodes header TSV file path> <edges header TSV file path> \
                                                <biolink version>
"""
import argparse
import csv
import json
import logging
import os
import statistics
import sys
from collections import defaultdict
from typing import Optional, Set, Dict

import jsonlines
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARRAY_DELIMITER = "ǂ"
ARRAY_COL_NAMES = {"all_names", "all_categories", "equivalent_curies", "publications", "kg2_ids"}
KGX_COL_NAME_REMAPPINGS = {
    "category": "preferred_category"
}
LITE_PROPERTIES = {"id", "name", "preferred_category", "all_categories",
                   "subject", "object", "predicate", "primary_knowledge_source",
                   "qualified_predicate", "qualified_object_aspect", "qualified_object_direction",
                   "domain_range_exclusion"}
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
    else:
        return value


def should_filter_out(row_obj: dict) -> bool:
    primary_ks = row_obj.get("primary_knowledge_source")
    publications = row_obj.get("publications")
    if primary_ks == "infores:semmeddb" and (not publications or len(publications) < 4):
        return True
    elif row_obj.get("domain_range_exclusion") in {True, "True", "true"}:
        return True
    else:
        return False


def write_rows_to_jsonl_file(rows: list, jsonl_file_path: Optional[str]):
    if rows and jsonl_file_path:
        with jsonlines.open(jsonl_file_path, mode="a") as jsonl_writer:
            jsonl_writer.write_all(rows)


def get_ancestors(node_id: str, child_to_parent_map: Dict[str, Set[str]],
                  child_to_ancestors_map: Dict[str, Set[str]], recursion_depth: int,
                  problem_nodes: Set[str]):
    # Adapted from the PloverDB code for building the concept descendant index
    if node_id not in child_to_ancestors_map:
        if recursion_depth > 20:
            logging.info(f"Hit recursion depth of 20 for node {node_id}; discarding this "
                         f"lineage (will write to problem file)")
            problem_nodes.add(node_id)
        else:
            for parent_id in child_to_parent_map.get(node_id, set()):
                parent_ancestors = get_ancestors(parent_id, child_to_parent_map, child_to_ancestors_map,
                                                 recursion_depth + 1, problem_nodes)
                child_to_ancestors_map[node_id] = child_to_ancestors_map[node_id].union({parent_id}, parent_ancestors)
    return child_to_ancestors_map.get(node_id, set())


def materialize_direct_subclass_edges(child_to_parents: defaultdict[str, Set[str]], edges_jsonl_file_path_filtered):
    # Adapted from the PloverDB code for building the concept descendant index
    # Maybe later don't create another copy of already existing direct edges (superclass complicates a little)
    logging.info(f"Materializing direct subclass_of edges for all indirect concept --> ancestor relationships")
    if child_to_parents:
        # Recursively derive all ancestors for each concept
        child_to_ancestors = defaultdict(set)
        problem_nodes = set()
        for child_node_id in child_to_parents:
            _ = get_ancestors(child_node_id, child_to_parents, child_to_ancestors, 0, problem_nodes)

        # Create direct edges for each child --> ancestor relationship (tack onto jsonl edges file)
        direct_subclass_edges = []
        for child_id, ancestor_ids in child_to_ancestors.items():
            for ancestor_id in ancestor_ids:
                edge = {
                    "subject": child_id,
                    "object": ancestor_id,
                    "predicate": "biolink:subclass_of",
                    "primary_knowledge_source": "infores:rtx-kg2",  # Maybe a better way of doing this? Not a great situation..
                    "id": f"materialized_subclass_relationship:{child_id}-->{ancestor_id}"
                }
                direct_subclass_edges.append(edge)
        # Note: Currently only add these direct subclass edges to the 'filtered' edges file, which Plater uses
        write_rows_to_jsonl_file(direct_subclass_edges, edges_jsonl_file_path_filtered)

        # Print out/save some useful stats
        logging.info(f"Calculating report stats..")
        node_to_num_ancestors = {node_id: len(ancestors) for node_id, ancestors in child_to_ancestors.items()}
        ancestor_counts = list(node_to_num_ancestors.values())
        prefix_counts = defaultdict(int)
        top_50_biggest_nodes = sorted(node_to_num_ancestors.items(), key=lambda x: x[1], reverse=True)[:50]
        for node_id in child_to_ancestors:
            prefix = node_id.split(":")[0]
            prefix_counts[prefix] += 1
        sorted_prefix_counts = dict(sorted(prefix_counts.items(), key=lambda count: count[1], reverse=True))
        report_path = f"{SCRIPT_DIR}/subclass_report.json"
        with open(report_path, "w+") as report_file:
            report = {
                "num_nodes_with_ancestors": {
                    "total": len(child_to_ancestors),
                    "by_prefix": sorted_prefix_counts
                },
                "num_ancestors_per_node": {
                    "mean": round(statistics.mean(ancestor_counts), 3),
                    "max": max(ancestor_counts),
                    "median": statistics.median(ancestor_counts),
                    "mode": statistics.mode(ancestor_counts)
                      },
                "problem_nodes": {
                    "count": len(problem_nodes),
                    "curies": list(problem_nodes)
                },
                "top_50_nodes_with_most_ancestors": {
                    "counts": {item[0]: item[1] for item in top_50_biggest_nodes},
                    "curies": [item[0] for item in top_50_biggest_nodes]
                },
                "example_mappings": {
                    "Diabetes mellitus (MONDO:0005015)": list(child_to_ancestors.get("MONDO:0005015", [])),
                    "Adams-Oliver syndrome (MONDO:0007034)": list(child_to_ancestors.get("MONDO:0007034", []))
                }
            }
            json.dump(report, report_file, indent=2)
        logging.info(f"Done with materializing direct subclass_of edges. Report is at {report_path}")
    else:
        logging.error(f"No child_to_parent map - cannot proceed with materializing direct subclass_of edges.")


def convert_tsv_to_jsonl(tsv_path: str, header_tsv_path: str, bh: any, kind: str):
    """
    This method assumes the input TSV file names are in KG2c format (e.g., like nodes_c.tsv and nodes_c_header.tsv)
    """
    logging.info(f"\n\n**** Starting to process file {tsv_path} (header file is: {header_tsv_path}) ****")
    jsonl_output_file_path = tsv_path.replace('.tsv', '.jsonl')
    jsonl_output_file_path_lite = tsv_path.replace('.tsv', '-lite.jsonl')
    jsonl_output_file_path_filtered = tsv_path.replace('.tsv', '-filtered.jsonl') if kind == "edges" else None
    logging.info(f"Output file path for full version will be: {jsonl_output_file_path}")
    logging.info(f"Output file path for lite version will be: {jsonl_output_file_path_lite}")
    logging.info(f"Output file path for filtered version will be: {jsonl_output_file_path_filtered}")

    # First delete preexisting versions of these files (important since we write in append mode)
    try:  # Rather crude way of making 'sudo' not be used on my Mac, but still be used on ubuntu instances..
        os.system(f"rm -f {jsonl_output_file_path}")
        os.system(f"rm -f {jsonl_output_file_path_lite}")
        os.system(f"rm -f {jsonl_output_file_path_filtered}")
    except Exception:
        os.system(f"sudo rm -f {jsonl_output_file_path}")
        os.system(f"sudo rm -f {jsonl_output_file_path_lite}")
        os.system(f"sudo rm -f {jsonl_output_file_path_filtered}")

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
    trusted_subclass_sources = {"infores:mondo", "infores:chebi"}  # These are the same as Plover uses for now

    logging.info(f"Starting to convert rows in {tsv_path} to json lines..")
    with open(tsv_path, "r") as input_tsv_file:
        batch = []
        batch_lite = []
        batch_filtered = []
        num_rows_processed = 0
        num_remapped_subclass_of_edges = 0
        num_edges_filtered_out = 0
        child_to_parents = defaultdict(set)
        tsv_reader = csv.reader(input_tsv_file, delimiter="\t")
        for line in tsv_reader:
            # Convert this row in the TSV into a json object
            row_obj = dict()
            for col_name in columns_to_keep:
                raw_value = line[node_column_indeces[col_name]]
                if raw_value not in {"", "{}", "[]", None}:  # Skip empty values, not false ones
                    kgx_col_name = KGX_COL_NAME_REMAPPINGS.get(col_name, col_name)
                    parsed_value = parse_value(raw_value, col_name)

                    if col_name == "all_categories":
                        # Expand categories to their ancestors as appropriate (Plater requires this pre-
                        # expansion), but also retain what the categories were pre-expansion
                        row_obj[kgx_col_name] = parsed_value
                        row_obj["category"] = bh.get_ancestors(parsed_value,
                                                               include_mixins=False,
                                                               include_conflations=False)  # Done at query time
                    else:
                        row_obj[kgx_col_name] = parsed_value

            # Raise the predicate of subclass_of edges from sources we don't want used for subclass reasoning
            predicate = row_obj.get("predicate")  # Will be None if this is a Node object
            primary_knowledge_source = row_obj.get("primary_knowledge_source")
            if predicate == "biolink:subclass_of" and primary_knowledge_source not in trusted_subclass_sources:
                row_obj["predicate"] = "biolink:related_to_at_concept_level"
                num_remapped_subclass_of_edges += 1

            # Save the row as applicable; create both the 'lite', 'full', and 'filtered' files at the same time
            batch.append(row_obj)
            batch_lite.append({property_name: value for property_name, value in row_obj.items()
                               if property_name in LITE_PROPERTIES})
            if kind == "edges":
                if not should_filter_out(row_obj):
                    batch_filtered.append(row_obj)

                    # Fill out our concept parent map as appropriate (used later to materialize direct subclass edges)
                    if row_obj["predicate"] in {"biolink:subclass_of", "biolink:superclass_of"}:
                        child = row_obj["subject"] if row_obj["predicate"] == "biolink:subclass_of" else row_obj["object"]
                        parent = row_obj["object"] if row_obj["predicate"] == "biolink:subclass_of" else row_obj["subject"]
                        child_to_parents[child].add(parent)
                else:
                    num_edges_filtered_out += 1

            # Write this batch of rows to the jsonl files if it's time
            if len(batch) == 1000000:
                write_rows_to_jsonl_file(batch, jsonl_output_file_path)
                write_rows_to_jsonl_file(batch_lite, jsonl_output_file_path_lite)
                write_rows_to_jsonl_file(batch_filtered, jsonl_output_file_path_filtered)
                num_rows_processed += len(batch)
                batch, batch_lite, batch_filtered = [], [], []
                logging.info(f"Have processed {num_rows_processed} rows... "
                             f"({num_edges_filtered_out} filtered out, {num_remapped_subclass_of_edges} "
                             f"subclass_of remapped)")

        # Take care of writing the (potential) final partial batch
        write_rows_to_jsonl_file(batch, jsonl_output_file_path)
        write_rows_to_jsonl_file(batch_lite, jsonl_output_file_path_lite)
        write_rows_to_jsonl_file(batch_filtered, jsonl_output_file_path_filtered)
        logging.info(f"Done writing final partial batch.")

    if kind == "edges":
        materialize_direct_subclass_edges(child_to_parents, jsonl_output_file_path_filtered)

    logging.info(f"Done converting rows in {tsv_path} to json lines.")
    logging.info(f"Line counts of output files:")
    logging.info(os.system(f"wc -l {jsonl_output_file_path}"))
    logging.info(os.system(f"wc -l {jsonl_output_file_path_lite}"))
    if kind == "edges":
        logging.info(os.system(f"wc -l {jsonl_output_file_path_filtered}"))


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("nodes_tsv_path", help="Path to the nodes TSV file you want to transform")
    arg_parser.add_argument("edges_tsv_path", help="Path to the edges TSV file you want to transform")
    arg_parser.add_argument("nodes_header_tsv_path", help="Path to the header TSV file for your nodes file")
    arg_parser.add_argument("edges_header_tsv_path", help="Path to the header TSV file for your edges file")
    arg_parser.add_argument("biolink_version", help="Version of Biolink to use")
    args = arg_parser.parse_args()
    logging.info(f"Input args are:\n {args}")

    # First download BiolinkHelper
    bh_file_name = "biolink_helper.py"
    logging.info(f"Downloading {bh_file_name} from RTX repo")
    local_path = f"{SCRIPT_DIR}/{bh_file_name}"
    remote_path = f"https://github.com/RTXteam/RTX/blob/master/code/ARAX/BiolinkHelper/{bh_file_name}?raw=true"
    os.system(f"curl -L {remote_path} -o {local_path}")
    from biolink_helper import BiolinkHelper
    bh = BiolinkHelper(biolink_version=args.biolink_version)

    # Then actually create the JSON lines files
    convert_tsv_to_jsonl(args.nodes_tsv_path, args.nodes_header_tsv_path, bh, "nodes")
    convert_tsv_to_jsonl(args.edges_tsv_path, args.edges_header_tsv_path, bh, "edges")

    logging.info(f"\n\nDone converting KG2c nodes/edges TSVs to KGX JSON lines format.")


if __name__ == "__main__":
    main()
