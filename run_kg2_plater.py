"""
This script loads a given KG2c version into Plater (and also Neo4j, which Plater uses).
For now this script should be run on the kg2cplover2.rtx.ai instance (until we get a
setup script written).
Usage: python <kg2_version, e.g., 2.8.4>
"""

import argparse
import logging
import os
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HOME_DIR = f"{SCRIPT_DIR}/.."
ORION_DIR = f"{HOME_DIR}/ORION_parent_dir/ORION"
ORION_GRAPHS_DIR = f"{HOME_DIR}/ORION_parent_dir/Data_services_graphs"

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    handlers=[logging.FileHandler("build.log"),
                              logging.StreamHandler()])


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("kg2_version", help="Version number for the KG2c you want to load")
    args = arg_parser.parse_args()
    logging.info(f"Input args are:\n {args}")

    start = time.time()

    # Download the proper KG2c TSVs
    logging.info(f"Downloading the proper KG2c TSVs..")
    local_kg2c_tarball_name = f"kg{args.kg2_version}c-tsv.tar.gz"
    os.system(f"scp rtxconfig@arax-databases.rtx.ai:/home/rtxconfig/KG${args.kg2_version}/extra_files/kg2c-tsv.tar.gz "
              f"{SCRIPT_DIR}/{local_kg2c_tarball_name}")
    os.system(f"tar -xvzf {SCRIPT_DIR}/{local_kg2c_tarball_name} -C {SCRIPT_DIR}")

    # Convert the TSVs to JSON lines format
    logging.info(f"Converting TSVs to JSON lines format..")
    os.system(f"pyenv activate plater-plover")
    os.system(f"python convert_kg2c_tsvs_to_jsonl.py nodes_c.tsv edges_c.tsv "
              f"nodes_c_header.tsv edges_c_header.tsv")

    # Move our JSON lines files into the ORION directory
    logging.info(f"Moving JSON lines files into ORION graphs dir..")
    os.system(f"mv {SCRIPT_DIR}/nodes_c.jsonl {ORION_GRAPHS_DIR}")
    os.system(f"mv {SCRIPT_DIR}/edges_c.jsonl {ORION_GRAPHS_DIR}")

    second_start = time.time()

    # Use ORION to create a neo4j dump based on our JSON lines files
    logging.info(f"Using ORION to create a neo4j dump based on our JSON lines files..")
    os.system(f"cd {ORION_DIR}")
    os.system(f'export DATA_SERVICES_STORAGE="$PWD/../Data_services_storage/"')
    os.system(f'export DATA_SERVICES_GRAPHS="$PWD/../Data_services_graphs/"')
    os.system(f'export DATA_SERVICES_LOGS="$PWD/../Data_services_logs/"')
    os.system(f'export DATA_SERVICES_GRAPH_SPEC=testing-graph-spec.yml')
    os.system(f'export DATA_SERVICES_NEO4J_PASSWORD=test')
    os.system(f'export DATA_SERVICES_OUTPUT_URL=https://localhost/')
    os.system(f'export PYTHONPATH="$PYTHONPATH:$PWD"')
    os.system(f"printenv")
    os.system(f"sudo -E docker-compose run --rm data_services "
              f"python /Data_services/cli/neo4j_dump.py "
              f"/Data_services_graphs/rtx-kg2.8.6c/ "
              f"nodes.jsonl edges.jsonl")

    # Load the ORION neo4j dump into a neo4j database
    logging.info(f"Loading the ORION neo4j dump into a neo4j database..")
    os.system(f"sudo docker run --interactive --tty --rm \
                --volume=$HOME/neo4j/data:/data \
                --volume=$HOME/neo4j_dumps:/backups \
                --env NEO4J_AUTH=neo4j/test \
                neo4j/neo4j-admin:4.4.10 \
                neo4j-admin load --database=neo4j --from=/backups/graph_.db.dump")

    # Start up the neo4j database
    logging.info(f"Starting up the neo4j database..")
    os.system(f'sudo docker run -d \
                    -p 7474:7474 -p 7687:7687 \
                    --name neo4j-kg{args.kg2_version}c \
                    --volume=$HOME/neo4j/data:/data \
                    --env NEO4J_AUTH=neo4j/test \
                    -e NEO4J_apoc_export_file_enabled=true \
                    -e NEO4J_apoc_import_file_enabled=true \
                    -e NEO4J_apoc_import_file_use__neo4j__config=true \
                    -e NEO4J_PLUGINS=\[\"apoc\"\] \
                    neo4j:4.4.10')

    # Start up Plater
    logging.info(f"Starting up Plater..")
    os.system(f"cd {HOME_DIR}/Plater")
    os.system(f"pyenv activate plater-plover")
    os.system(f"./main.sh")

    logging.info(f"Done. Plater should be working! Took {round((time.time() - start) / 60)} "
                 f"minutes starting from TSVs; {round((time.time() - second_start) / 60)} "
                 f"minutes excluding conversion from TSVs to jsonl.")


if __name__ == "__main__":
    main()
