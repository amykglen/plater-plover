# Meant to be run on the kg2cplover instance (or whatever instance you want to send tests FROM)

is_set_flag=$1

cd ~/plater-plover/test
rm plater.tsv
git pull origin main
. ${HOME}/.pyenv/versions/plater-ploverenv/bin/activate

plater_endpoint=http://kg2cplover2.rtx.ai:8080/1.4

pytest -vs test.py -k test_specified --querypath sample_kg2_queries_ITRBPROD ${is_set_flag} --endpoint ${plater_endpoint}
pytest -vs test.py -k test_specified --querypath sample_kg2_queries_ANYKG2 ${is_set_flag} --endpoint ${plater_endpoint}
pytest -vs test.py -k test_specified --querypath sample_kg2_queries_LONG ${is_set_flag} --endpoint ${plater_endpoint}