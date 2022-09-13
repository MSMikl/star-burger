#!/bin/bash
set -e
cd ~/python/star-burger
git pull
source venv/bin/activate
pip install -r requirements.txt
npm ci --dev
./node_modules/.bin/parcel watch bundles-src/index.js --dist-dir bundles --public-url="./"
python3 manage.py migrate
systemctl restart burger-server
systemctl reload nginx
echo 'Deployment successful'
