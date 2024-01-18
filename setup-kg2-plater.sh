
neo4j_password="$1"

# General setup
pyenv install 3.10.6
pyenv virtualenv 3.10.6 plater-ploverenv
cd "$(dirname "$0")"  # This is the directory containing this script ('plater-plover')
. ${HOME}/.pyenv/versions/plater-ploverenv/bin/activate pip install -r requirements.txt

# Set up for ORION
mkdir -m 777 ~/ORION_parent_dir
cd ~/ORION_parent_dir
mkdir -m 777 Data_services_graphs
mkdir -m 777 Data_services_logs
mkdir -m 777 Data_services_storage
git clone https://github.com/RobokopU24/ORION.git

# Set up for Plater
git clone https://github.com/TranslatorSRI/Plater
cd Plater
cp .env-template .env
echo "NEO4J_PASSWORD=${neo4j_password}" >> .env
pyenv virtualenv 3.10.6 platerenv
. ${HOME}/.pyenv/versions/platerenv/bin/activate pip install -r PLATER/requirements.txt



