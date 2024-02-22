# plater-plover

This repo provides scripts/documentation for hosting RTX-KG2 using **1)** the Plater stack 
and **2)** the Plover stack. 

We assume you are using an Ubuntu instance; we used `kg2cplover2.rtx.ai`, which is an 
r5a.4xlarge EC2 instance (128GiB RAM) running Ubuntu 18.04.

And we assume your instance has the following installed:
* Docker; we used version 24.0.2
* docker-compose; we installed version 1.29.2 using curl:
  ```
  sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  sudo mv /usr/local/bin/docker-compose /usr/bin
  ```
* pyenv and virtualenv, with python 3.10.6 installed; we used these commands (from [this guide](https://akrabat.com/creating-virtual-environments-with-pyenv/)):
  ```
  sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl git
  curl https://pyenv.run | bash
  pyenv install 3.10.6
  ```
In addition, your instance's public RSA key will need to be added to the `authorized_keys` on the
`arax-databases.rtx.ai` instance.


## 1. Hosting KG2 in the Plater stack

Before starting, ensure that **port 8080 is open** on the instance you will be serving KG2 Plater from.

Then run the instance setup script, specifying whatever password you want to use for neo4j:
```
bash -x setup-kg2-plater.sh myneo4jpassword
```
Note that the setup script only needs to be run once per instance.

Then actually build KG2 Plater, specifying which KG2c and Biolink versions to use (mostly consists of loading KG2c into Neo4j):
```
bash -x kg2-plater-build.sh 2.8.4 3.1.2 myneo4jpassword
```

Then serve/run Plater, again specifying the KG2c version and your neo4j password:
```
bash -x run-kg2-plater.sh 2.8.4 myneo4jpassword
```

At this point you should be able to query KG2 Plater at port 8080. For instance, if you serve Plater on the 
`myinstance.rtx.ai` AWS EC2 instance, you should be able to query it at:
```
http://myinstance.rtx.ai:8080/1.4/query
```

## 2. Hosting KG2 in the Plover stack

TODO
