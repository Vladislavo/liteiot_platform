pip3 install virtualenv
python3 -m virtualenv env
source env/bin/activate

sudo apt-get install -y postgresql postgresql-contrib
sudo apt-get install -y libpq-dev

sudo apt-get install -y libssl-dev

pip install -r app/requirements.txt

sudo -u postgres psql -c "CREATE USER ${USER} WITH PASSWORD 'dev';"
sudo -u postgres psql -c "CREATE DATABASE iotserver WITH OWNER=${USER};"
psql -d iotserver -f db.sql

mkdir app/app/data

export FLASK_APP=run.py
export FLASK_ENV=production
