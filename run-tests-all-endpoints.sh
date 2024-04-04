# Usage: bash -x run-tests-all-endpoints.sh <pytest is_set flag, e.g.: --issetfalse>
# Run this script on whatever instance you want to send tests FROM. Requires having run setup-kg2-plater.sh

is_set_flag=$1

cd ~/plater-plover
git pull origin main
. ${HOME}/.pyenv/versions/plater-ploverenv/bin/activate

bash -x run-tests.sh http://amyplater.rtx.ai:8080/1.4 ${is_set_flag}
bash -x run-tests.sh http://amyplover.rtx.ai:9990 ${is_set_flag}
bash -x run-tests.sh http://amyaraxkg2.rtx.ai:8080/api/rtxkg2/v1.4 ${is_set_flag}