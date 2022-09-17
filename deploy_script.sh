#!/bin/bash
set -e
cd ~/python/star-burger
git pull
version=`git rev-parse HEAD`
source venv/bin/activate
pip install -r requirements.txt
python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput
systemctl restart burger-server
systemctl reload nginx
 curl -H "X-Rollbar-Access-Token: 452fe41d343c43c78ed9bb6787c71afb" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "production_server", "revision": "'${version}'", "rollbar_name": "mikl", "local_username": "mikl", "comment": "", "status": "succeeded"}'
echo 'Deployment successful'
