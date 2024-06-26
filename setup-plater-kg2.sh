# Usage: bash -x setup-plater-kg2.sh <neo4j_password_to_use>

neo4j_password="$1"
set -e  # Stop on error

# General setup
set +e  # Temporarily don't stop on error, in case this pyenv already exists
pyenv virtualenv 3.10.6 plater-ploverenv
set -e
cd "$(dirname "$0")"  # This is the directory containing this script ('plater-plover')
"${HOME}/.pyenv/versions/plater-ploverenv/bin/pip" install -r requirements.txt

# Set up for ORION
mkdir -p -m 777 ~/ORION_parent_dir
cd ~/ORION_parent_dir
mkdir -p -m 777 Data_services_graphs
mkdir -p -m 777 Data_services_logs
mkdir -p -m 777 Data_services_storage
if [ ! -d "ORION" ]; then
  git clone https://github.com/RobokopU24/ORION.git --branch litcoin-test-6  # This is a release from Jan. 2024
fi

# TODO: check out specific branch? or merge my eventual final branch into master?
# Set up for Plater
cd ~
if [ ! -d "Plater" ]; then
  git clone https://github.com/amykglen/Plater.git
fi
cd Plater
git checkout subclasscypher  # Runs Plater 1.5.0 with slight modifications
git pull origin subclasscypher
cp .env-template .env
echo "NEO4J_PASSWORD=${neo4j_password}" >> .env
set +e  # Temporarily don't stop on error, in case this pyenv already exists
pyenv virtualenv 3.10.6 platerenv
set -e
"${HOME}/.pyenv/versions/platerenv/bin/pip" install -r PLATER/requirements.txt



