#!/usr/bin/env bash
set -euxo pipefail
mkdir -p /opt/lab5 && cd /opt/lab5
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip git
if [ ! -d flask-tutorial ]; then
  git clone https://github.com/cu-csci-4253-datacenter/flask-tutorial || true
fi
cd flask-tutorial
python3 setup.py install || true
pip3 install -e .
export FLASK_APP=flaskr
# for newer Flask CLIs you can also do: flask --app flaskr init-db
flask init-db || true
# for newer Flask CLIs you can also do: nohup flask --app flaskr run -h 0.0.0.0 -p 5000 >/var/log/flaskr.log 2>&1 &
nohup flask run -h 0.0.0.0 -p 5000 >/var/log/flaskr.log 2>&1 &
