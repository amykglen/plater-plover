# Usage: bash -x run-plater-kg2.sh <kg2_version, e.g., 2.8.4> <biolink_version, e.g., 3.1.2> <neo4j_password>

kg2_version="$1"
biolink_version="$2"
neo4j_password="$3"

cd ~/plater-plover

bash -x setup-plater-kg2.sh ${neo4j_password}
bash -x build-plater-kg2.sh ${kg2_version} ${biolink_version} ${neo4j_password}
bash -x start-plater-kg2.sh ${kg2_version} ${neo4j_password}