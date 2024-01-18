# plater-plover


## 1. Setting up

This section describes how to set up an instance for hosting KG2 in Plater (i.e., setting up to run the 
`run-kg2-plater.sh` script).

It assumes you're using an Ubuntu instance with Docker installed. We used kg2cplover2.rtx.ai, which is an 
r5a.4xlarge EC2 instance (128GB RAM) running Ubuntu 18.04.

TODO: add summary. need three repos, each with a bit of setup. 


### General set up

TODO: clone plater-plover. change section name.

Your instance's public RSA key will need to be added to `authorized_keys` under the 
`rtxconfig` user on `arax-databases.rtx.ai`.


### Set up for ORION

First you need to install `docker-compose` on your instance - we installed version 1.29.2 using `sudo apt-get`.

Then clone the ORION repo into a parent directory (named as shown):

```
mkdir -m 777 ~/ORION_parent_dir
cd ~/ORION_parent_dir
git clone https://github.com/RobokopU24/ORION.git
```

Then set up some more necessary directories (note: ORION provides an env setup script, but it didn't work 
quite right - I've extracted the relevant pieces here):

```
cd ~/ORION_parent_dir
mkdir -m 777 Data_services_graphs
mkdir -m 777 Data_services_logs
mkdir -m 777 Data_services_storage
```


### Set up for Plater

Clone the repo and start setting up the .env file:
```
git clone https://github.com/TranslatorSRI/Plater
cd Plater
cp .env-template .env
```

Then add the following line to the .env file:
```
NEO4J_PASSWORD=test
```

Then create a virtual environment and install requirements:
```
pyenv virtualenv 3.10.6 plater-plover
cd Plater
pip install -r PLATER/requirements.txt
```
(We're assuming you have pyenv installed.)



## 2. Serving KG2

### Using Plater

TODO. activate the plater-plover pyenv.

then do run-kg2-plater.sh passing in proper kg2 version and neo4j password.

### Using Plover

TODO.
