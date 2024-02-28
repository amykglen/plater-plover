
# First delete any potential duplicate containers/images
set +e  # Temporarily don't stop on error, in case this container doesn't already exist
sudo docker stop kg2
sudo docker rm kg2
sudo docker image rm arax:kg2
set -e  # Go back to stopping on error

# Build the image
sudo docker build --no-cache=true --rm -t arax:kg2 ./DockerBuild/ -f ./DockerBuild/KG2-Dockerfile

# Run the container
sudo docker run -d -it --name kg2 -v /mnt/data/orangeboard/databases:/mnt/data/orangeboard/databases -v /mnt/config/plover_url_override.txt:/mnt/data/orangeboard/kg2/RTX/code/plover_url_override.txt -v /mnt/config/config_secrets.json:/mnt/data/orangeboard/kg2/RTX/code/config_secrets.json -p 8080:80 arax:kg2

# Create database symlinks
sudo docker exec kg2 bash -c "sudo -u rt bash -c 'cd /mnt/data/orangeboard/kg2/RTX && python3 code/ARAX/ARAXQuery/ARAX_database_manager.py'"

# Start the application
sudo docker exec kg2 bash -c "service apache2 start"
sudo docker exec kg2 bash -c "service RTX_OpenAPI_kg2 start"