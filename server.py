from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import bcrypt
import misc
import dao.user.user as ud


APP_KEY_LEN = 8


server = Flask(__name__, template_folder='templates/')


def get_apps(username):
    res = []
    try:
        conn = psycopg2.connect('dbname=gateway')
        cur  = conn.cursor()
        query = """
        SELECT * FROM
            applications
        WHERE 
            username = %s
        """
        cur.execute(query, (username,))
        res = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print('Error querying applications: ', error)
    finally:
        if (conn):
            cur.close()
            conn.close()
        
    return res



def get_app(appkey):
    res = []
    try:
        conn = psycopg2.connect('dbname=gateway')
        cur  = conn.cursor()
        query = """
        SELECT * FROM
            applications
        WHERE 
            app_key = %s
        """
        cur.execute(query, (appkey,))
        res = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print('Error querying applications: ', error)
    finally:
        if (conn):
            cur.close()
            conn.close()
        
    return res




def new_app(name, desc):
    suc = (True, 'App created')
    try:
        conn = psycopg2.connect('dbname=gateway')
        cur  = conn.cursor()
        query = """
        INSERT INTO
            applications
        VALUES
            (%s, %s, %s, %s)
        """
        cur.execute(query, (name, misc.rand_str(APP_KEY_LEN), session['name'], desc))
        conn.commit()
        print('App created')
    except (Exception, psycopg2.DatabaseError) as error:
        print('Error creating app: ', error)
        suc = (False, error)
    finally:
        if (conn):
            cur.close()
            conn.close()
        
    return suc



def new_app_devs(appkey):
    suc = (True, 'app_devs created')
    try:
        conn = psycopg2.connect('dbname=gateway')
        cur  = conn.cursor()
        query = """
        CREATE TABLE devs_%s (
            name VARCHAR(30) NOT NULL,
            dev_id NUMERIC(3) PRIMARY KEY,
            app_key VARCHAR(80),
            description VARCHAR(200)
            FOREIGN KEY (app_key) REFERENCES applications(app_key)
        );
        """
        cur.execute(query, (appkey,))
        conn.commit()
        print('Devs table created')
    except (Exception, psycopg2.DatabaseError) as error:
        print('Error creating devs table: ', error)
        suc = (False, error)
    finally:
        if (conn):
            cur.close()
            conn.close()
        
    return suc





def get_devs(appkey):
    res = []
    try:
        conn = psycopg2.connect('dbname=gateway')
        cur  = conn.cursor()
        query = """
        SELECT * FROM
            devs-%s
        """
        cur.execute(query, (appkey,))
        res = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print('Error querying applications: ', error)
    finally:
        if (conn):
            cur.close()
            conn.close()
        
    return res





@server.route('/')
def index():
    if 'name' in session and len(session['name']) > 0:
        apps = get_apps(session['name'].encode('utf-8'))
        print('apps: ', apps)
        return render_template('index.html', apps=apps)

    return render_template('index.html')



@server.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else: 
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        if (username == '' or password == ''):
            feedback = 'Username or password fields cannot be empty'
            return render_template('signup.html', feedback=feedback)
        else:
            uh = ud.UserDao()
            res = uh.create(username, password)
            if (not res[0]):
                return render_template('signup.html', feedback=res[1])
            else:
                session['name'] = username
        
                return redirect(url_for('index'))



@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else: 
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        if (username == '' or password == ''):
            feedback = 'Username or password fields cannot be empty'
            return render_template('login.html', feedback=feedback)
        else:
            uh = ud.UserDao()
            res = uh.get(username, password)
            if (not res[0]):
                return render_template('login.html', feedback=msg[1])
            else:
                session['name'] = username
        
                return redirect(url_for('index'))



@server.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))



@server.route('/new-app')
def new_application():
    return render_template('new-app.html')



@server.route('/app', methods=['GET', 'POST'])
def app():
    if request.method == 'GET':
        app = get_app(request.form['appkey'])
        devs = get_devs(app[1])
        
        return render_template('app.html', app=app, devs=devs)
    else:
        if request.form['appname'] == '':
            error = 'Application name cannot be empty.'
            return render_template('new-app.html', feedback=error)
        else:
            res = new_app(request.form['appname'], request.form['appdesc'])
            if not res[0]:
                return render_template('new-app.html', feedback=res[1])

            res = new_app_devs(request.form['appname'])
            if not res[0]:
                rm_app(request.form['appname'])
                return render_template('new-app.html', feedback=res[1])
            
            if not res[0] or not rer[0]:
                return render_template('new-app.html', feedback=str(res[1])+'|'+str(rer[1]))
            else:
                return redirect(url_for('index'))


if __name__ == '__main__':
    server.secret_key = 'sdjfklsjf^$654sd^#sPH'
    server.run(debug = True, host='0.0.0.0')


