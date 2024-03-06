# Meant to be run on the kg2cplover instance (or whatever instance you want to send tests FROM)

cd ~/plater-plover/test
rm plover.tsv
git pull origin main
. ${HOME}/.pyenv/versions/plater-ploverenv/bin/activate
pytest -vs test.py -k test_kg2_sample --endpoint http://kg2cplover2.rtx.ai:8080/api/rtxkg2/v1.4