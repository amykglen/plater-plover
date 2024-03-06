# Meant to be run on the kg2cplover instance (or whatever instance you want to send tests FROM)

screen -S test
cd ~/plater-plover/test
rm plater.tsv
git pull origin main
pyenv activate plater-ploverenv
pytest -vs test.py -k test_kg2_sample --endpoint http://kg2cplover2.rtx.ai:8080/1.4