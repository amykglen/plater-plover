import csv
import os
from collections import defaultdict

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_COLS = ["duration_server", "duration_db", "response_status", "num_results", "num_nodes", "num_edges"]
COLWISE = 0
ROWWISE = 1


def convert_to_right_type(value: str):
    if value == "":
        return None
    elif "." in value:
        return float(value)
    else:
        return int(value)


def main():
    is_set_kinds = ["asis", "issetfalse", "issettrue"]
    stacks = ["araxkg2", "plater", "plover"]
    runs = [1, 2, 3]

    table_cols = ["platform", "query_id"] + [f"{base_col_name}_{run_num}" for run_num in runs
                                             for base_col_name in BASE_COLS]
    print(table_cols)

    for kind in is_set_kinds:
        print(f"\nStarting kind: {kind}")
        results_table = []

        for stack in stacks:
            print(f"  Starting stack: {stack}")
            stack_results = defaultdict(list)  # Maps query IDs for this platform to its merged data for all 3 runs

            for run in runs:
                print(f"    Starting run: {run}")
                results_tsv_path = f"{SCRIPT_DIR}/results/final_results/{kind}_results/{stack}--{kind}--{run}.tsv"

                results_dict = dict()
                with open(results_tsv_path, "r") as results_file:
                    reader = csv.reader(results_file, delimiter="\t")
                    next(reader)  # Skip the header row
                    for row in reader:
                        # Add the results for this run to the entry for this query ID (in this platform's results)
                        query_id = row[0]
                        row_relevant = row[3:-1]
                        row_preprocessed = [convert_to_right_type(value) for value in row_relevant]
                        stack_results[query_id] += row_preprocessed

            for query_id, results in stack_results.items():
                row = [stack, query_id] + results
                results_table.append(row)

        results_df_for_kind = pd.DataFrame(results_table, columns=table_cols)
        print(results_df_for_kind)
        results_df_for_kind.to_csv(f"results_{kind}.tsv", sep="\t")


if __name__ == "__main__":
    main()
