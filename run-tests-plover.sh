# Meant to be run on the kg2cplover instance (or whatever instance you want to send tests FROM)

cd ~/plater-plover/test
rm plover.tsv
git pull origin main
. ${HOME}/.pyenv/versions/plater-ploverenv/bin/activate

plover_endpoint=http://kg2cplover2.rtx.ai:8080/api/rtxkg2/v1.4

pytest -vs test.py -k test_directory_of_json_queries --querydir sample_kg2_queries_ITRBPROD --endpoint ${plover_endpoint}
pytest -vs test.py -k test_directory_of_json_queries --querydir sample_kg2_queries_ANYKG2 --endpoint ${plover_endpoint}
pytest -vs test.py -k test_directory_of_json_queries --querydir sample_kg2_queries_LONG --endpoint ${plover_endpoint}