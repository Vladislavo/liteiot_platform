pip3 install virtualenv
python3 -m virtualenv env
source env/bin/activate

sudo apt-get install libpq-dev

pip install -r requirements.txt

export FLASK_ENV=production
