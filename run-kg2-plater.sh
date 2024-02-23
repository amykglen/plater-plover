: ' This script runs Plater for a given KG2c version. Prior to running this script you need to have run the
build-kg2-plater.sh script for the given KG2c version (to prep the Neo4j database that Plater will query behind
the scenes).
Usage: bash -x run-kg2-plater.sh <kg2_version, e.g., 2.8.4> <neo4j_password>
'

kg2_version="$1"
neo4j_password="$2"
set -e  # Stop on error
neo4j_container_name=neo4j-kg${kg2_version}c

# First delete any potential duplicate neo4j container
set +e  # Temporarily don't stop on error, in case this container doesn't already exist
sudo docker stop ${neo4j_container_name}
sudo docker rm ${neo4j_container_name}
set -e  # Go back to stopping on error

# Start up the neo4j database/server that Plater will query behind the scenes
sudo docker run -d \
                -p 7474:7474 -p 7687:7687 \
                --name ${neo4j_container_name} \
                --volume=$HOME/neo4j/data:/data \
                --env NEO4J_AUTH=neo4j/${neo4j_password} \
                renciorg/neo4j-4.4.10-apoc-gds:0.0.1

sleep 2m  # Wait for neo4j to start up

# Start up Plater
cd ~/Plater
. ${HOME}/.pyenv/versions/platerenv/bin/activate
./main.sh
