# HPC&A IoT Server

The server is written in Python using [Flask][flask] framework and run on [uWSGI][uwsgi] server.
## Installation

1. Create forder for the server 
``` 
$ mkdir hpca_iot 
$ cd hpca_iot 
``` 
2. Clone the project 
``` 
$ git clone https://lorca.act.uji.es/gitlab/vrykov/thso.server/-/tree/dev 
$ cd thso.server 
```
3. Run preinstallation script which will create virtual envoronment, install all necessary C libs and python dependencies, and export environment variables. 
``` 
$ sudo ./preset.sh 
``` 

Now the server is installed and ready for configuration.

## Configuration

There are 3 types of configuration: environment, application and server. The environment can be production, 
development and testing. The server can run completely differently for each environment depending on your 
confuguration respectievely. The default environment is 'production'. ('production' environment requires for https and 
certificate precence for secure session management. If don't have, change to development environemt, which does not 
use encryption for session data). 
``` 
$ export FLASK_ENV=production 
$ export FLASK_ENV=development 
$ export FLASK_ENV=test 
``` 

The application configuration is basically describes database connection and other parameters as 
secure cookies or debug mode. On the other hand you have server (uWSGI) configuration which is located in 
app/server.ini. In this file you can define concurrency parameters as how many processes and threads will be used by 
the server or on which port it will be listening. For more information refer to [this link][uwsgiconf].

## Running

To run the server execute next command 
``` 
thso.server/app $ uwsgi aserver.ini 
``` 

[flask]: <https://flask.palletsprojects.com/en/1.1.x/> 
[uwsgi]: <https://uwsgi-docs.readthedocs.io/en/latest/> 
[uwsgiconf]: <https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html>
