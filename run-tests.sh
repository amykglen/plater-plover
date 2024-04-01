# Usage: bash -x run-tests.sh <KG2 stack endpoint, e.g.: http://amyplover.rtx.ai:9990> <pytest is_set flag, e.g.: --issetfalse>
# Run this script on whatever instance you want to send tests FROM. Requires having run setup-kg2-plater.sh

endpoint=$1
is_set_flag=$2

cd ~/plater-plover/test
git pull origin main
. ${HOME}/.pyenv/versions/plater-ploverenv/bin/activate

pytest -vs test.py -k test_specified --querypath sample_kg2_queries_ITRBPROD ${is_set_flag} --endpoint ${endpoint}
pytest -vs test.py -k test_specified --querypath sample_kg2_queries_ANYKG2 ${is_set_flag} --endpoint ${endpoint}
pytest -vs test.py -k test_specified --querypath sample_kg2_queries_LONG ${is_set_flag} --endpoint ${endpoint}
pytest -vs test.py -k test_specified --querypath sample_hand_crafted ${is_set_flag} --endpoint ${endpoint}