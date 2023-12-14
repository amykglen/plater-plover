

kg2_version="$1"
orion_kg2_subdir_name=rtx-kg${kg2_version}c
orion_kg2_subdir_path=~/ORION_parent_dir/Data_services_graphs/${orion_kg2_subdir_name}
neo4j_container_name=neo4j-kg${kg2_version}c

pyenv activate plater-plover

# Download the proper KG2c TSVs
cd ~/plater-plover  # This should be the directory containing this script
local_kg2c_tarball_name=kg${kg2_version}c-tsv.tar.gz
scp rtxconfig@arax-databases.rtx.ai:/home/rtxconfig/KG${kg2_version}/extra_files/kg2c-tsv.tar.gz ${local_kg2c_tarball_name}
tar -xvzf ${local_kg2c_tarball_name}

# Convert the TSVs to JSON lines format
python convert_kg2c_tsvs_to_jsonl.py nodes_c.tsv edges_c.tsv nodes_c_header.tsv edges_c_header.tsv

# Move the JSON lines files into the ORION directory
mkdir -m 777 ${orion_kg2_subdir_path}
mv nodes_c.jsonl ${orion_kg2_subdir_path}
mv edges_c.jsonl ${orion_kg2_subdir_path}

# Make sure environmental variables are set for ORION
cd ~/ORION_parent_dir/ORION
export DATA_SERVICES_STORAGE="$PWD/../Data_services_storage/"
export DATA_SERVICES_GRAPHS="$PWD/../Data_services_graphs/"
export DATA_SERVICES_LOGS="$PWD/../Data_services_logs/"
export DATA_SERVICES_GRAPH_SPEC=testing-graph-spec.yml
export DATA_SERVICES_NEO4J_PASSWORD=test
export DATA_SERVICES_OUTPUT_URL=https://localhost/
export PYTHONPATH="$PYTHONPATH:$PWD"
printenv

# Use ORION to create a Neo4j dump based on our json lines files
sudo -E docker-compose run --rm data_services \
         python /Data_services/cli/neo4j_dump.py \
         /Data_services_graphs/${orion_kg2_subdir_name}/ nodes_c.jsonl edges_c.jsonl

# Load the ORION Neo4j dump into a Neo4j database (goes into /home/ubuntu/neo4j/data area..)
# WARNING: If you don't want /home/ubuntu/neo4j/data to be overwritten, move it before running this part..
sudo docker run --interactive --tty --rm \
                --volume=$HOME/neo4j/data:/data \
                --volume=$HOME/ORION_parent_dir/Data_services_graphs/${orion_kg2_subdir_name}:/backups \
                --env NEO4J_AUTH=neo4j/test \
                neo4j/neo4j-admin:4.4.10 \
                neo4j-admin load --database=neo4j --from=/backups/graph_.db.dump

# Start up the Neo4j database
sudo docker rm ${neo4j_container_name}
sudo docker run -d \
                -p 7474:7474 -p 7687:7687 \
                --name ${neo4j_container_name} \
                --volume=$HOME/neo4j/data:/data \
                --env NEO4J_AUTH=neo4j/test \
                -e NEO4J_apoc_export_file_enabled=true \
                -e NEO4J_apoc_import_file_enabled=true \
                -e NEO4J_apoc_import_file_use__neo4j__config=true \
                -e NEO4J_PLUGINS=\[\"apoc\"\] \
                neo4j:4.4.10

# Start up Plater
cd ~/Plater
./main.sh