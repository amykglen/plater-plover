# plater-plover

This repo provides scripts/documentation for hosting RTX-KG2 using **1)** the Plater stack 
and **2)** the Plover stack. 

We assume you are using an Ubuntu instance; we used `kg2cplover2.rtx.ai`, which is an 
r5a.4xlarge EC2 instance (128GiB RAM) running Ubuntu 18.04.

We assume your instance has the following installed:
* Docker; we used version 24.0.2
* docker-compose; we installed version 1.29.2 using `sudo apt-get`
* pyenv and virtualenv

In addition, your instance's public RSA key will need to be added to the `authorized_keys` on the
`arax-databases.rtx.ai` instance.


## 1. Hosting KG2 in the Plater stack

First run the setup script, specifying whatever password you want to use for neo4j:
```
bash -x setup-kg2-plater.sh myneo4jpassword
```
Note that the setup script only needs to be run once per instance.

Then actually load KG2 into Plater and serve it, specifying whatever version of KG2 you would like to use as well as your neo4j password:
```
bash -x run-kg2-plater.sh 2.8.4 myneo4jpassword
```


## 2. Hosting KG2 in the Plover stack

