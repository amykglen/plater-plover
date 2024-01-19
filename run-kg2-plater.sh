: ' This script loads a given KG2c version into Plater (and also Neo4j, which Plater uses). It downloads
the KG2c TSV files from arax-databases.rtx.ai, so your RSA key must already be on that instance. Prior to running
this script you need to run the setup-kg2-plater.sh script to get your environment ready (only needs to be done once).
Usage: bash -x run-kg2-plater.sh <kg2_version, e.g., 2.8.4> <biolink_version, e.g., 3.5.2> <neo4j_password>
'

kg2_version="$1"
biolink_version="$2"
neo4j_password="$3"
set -e  # Stop on error

orion_kg2_subdir_name=rtx-kg${kg2_version}c
orion_kg2_subdir_path=~/ORION_parent_dir/Data_services_graphs/${orion_kg2_subdir_name}
neo4j_container_name=neo4j-kg${kg2_version}c

# Download the proper KG2c TSVs
cd "$(dirname "$0")"  # This is the directory containing this script ('plater-plover')
local_kg2c_tarball_name=kg${kg2_version}c-tsv.tar.gz
scp rtxconfig@arax-databases.rtx.ai:/home/rtxconfig/KG${kg2_version}/extra_files/kg2c-tsv.tar.gz ${local_kg2c_tarball_name}
tar -xvzf ${local_kg2c_tarball_name}

# Convert the TSVs to JSON lines format
"${HOME}/.pyenv/versions/plater-ploverenv/bin/python" convert_kg2c_tsvs_to_jsonl.py \
                                                                  nodes_c.tsv \
                                                                  edges_c.tsv \
                                                                  nodes_c_header.tsv \
                                                                  edges_c_header.tsv \
                                                                  ${biolink_version}

# Move the JSON lines files into the ORION directory
mkdir -p -m 777 ${orion_kg2_subdir_path}
mv nodes_c.jsonl ${orion_kg2_subdir_path}
mv edges_c.jsonl ${orion_kg2_subdir_path}

# Make sure environmental variables are set for ORION
cd ~/ORION_parent_dir/ORION
export DATA_SERVICES_STORAGE="$PWD/../Data_services_storage/"
export DATA_SERVICES_GRAPHS="$PWD/../Data_services_graphs/"
export DATA_SERVICES_LOGS="$PWD/../Data_services_logs/"
export DATA_SERVICES_GRAPH_SPEC=testing-graph-spec.yml
export DATA_SERVICES_NEO4J_PASSWORD=${neo4j_password}
export DATA_SERVICES_OUTPUT_URL=https://localhost/
export PYTHONPATH="$PYTHONPATH:$PWD"
printenv

# Use ORION to create a fresh Neo4j dump based on our json lines files
if test -f /Data_services_graphs/${orion_kg2_subdir_name}/graph_.db.dump; then
  sudo rm -rf /Data_services_graphs/${orion_kg2_subdir_name}/graph_.db.dump
fi
sudo -E docker-compose run --rm data_services \
         python /Data_services/cli/neo4j_dump.py \
         /Data_services_graphs/${orion_kg2_subdir_name}/ nodes_c.jsonl edges_c.jsonl

# Load the ORION Neo4j dump into a Neo4j database (goes into /home/ubuntu/neo4j/data area..)
# WARNING: If you don't want /home/ubuntu/neo4j/data to be deleted, move it before running this part..
if test -d $HOME/neo4j; then
  sudo rm -rf $HOME/neo4j
fi
# TODO: Figure out if this is the problem... need to delete any of its containers though before can delete the image
# TODO: Confirmed the nodes_c.jsonl file in data services graphs is good, so somewhere old data is getting loaded in..
set +e
sudo docker image rm orion_data_services
set -e
sudo docker pull renciorg/neo4j-4.4.10-apoc-gds:0.0.1
sudo docker run --interactive --tty --rm \
                --name temp_orion_neo4j
                --volume=$HOME/neo4j/data:/data \
                --volume=$HOME/ORION_parent_dir/Data_services_graphs/${orion_kg2_subdir_name}:/backups \
                --env NEO4J_AUTH=neo4j/${neo4j_password} \
                renciorg/neo4j-4.4.10-apoc-gds:0.0.1 \
                neo4j-admin load --database=neo4j --from=/backups/graph_.db.dump

# Delete any pre-existing containers
set +e  # Temporarily don't exit on errors, in case a container doesn't already exist by this name
sudo docker stop temp_orion_neo4j
sudo docker rm temp_orion_neo4j
sudo docker stop ${neo4j_container_name}
sudo docker rm ${neo4j_container_name}
set -e  # Switch back to exiting on error

# Start up the neo4j database
sudo docker run -d \
                -p 7474:7474 -p 7687:7687 \
                --name ${neo4j_container_name} \
                --volume=$HOME/neo4j/data:/data \
                --env NEO4J_AUTH=neo4j/${neo4j_password} \
                renciorg/neo4j-4.4.10-apoc-gds:0.0.1

# Start up Plater
cd ~/Plater
. ${HOME}/.pyenv/versions/platerenv/bin/activate
./main.sh