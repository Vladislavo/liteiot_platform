from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import bcrypt
import misc


APP_KEY_LEN = 8


server = Flask(__name__, template_folder='templates/')



def new_user(name, password):
    suc = (True, 'User added')
    try:
        conn = psycopg2.connect('dbname=gateway')
        cur  = conn.cursor()
        query = """
        INSERT INTO
            users
        VALUES
            (%s, %s)
        """
        cur.execute(query, (name, bcrypt.hashpw(password, bcrypt.gensalt())))
        conn.commit()
        print('User added')
    except (Exception, psycopg2.DatabaseError) as error:
        print('Error adding a user: ', error)
        suc = (False, error)
    finally:
        if (conn):
            cur.close()
            conn.close()
        
    return suc



def chk_user(name, password):
    suc = (True, 'Success')
    try:
        conn = psycopg2.connect('dbname=gateway')
        cur  = conn.cursor()
        query = """
        SELECT * FROM
            users
        WHERE 
            name = %s
        """
        cur.execute(query, (name,))
        user = cur.fetchall()[0]
        
        if user[1].encode('utf-8') == bcrypt.hashpw(password, user[1].encode('utf-8')):
            session['name'] = user[0]
            print('User logged in')
        else:
            suc = (False, 'Password or username do not match')
    except (Exception, psycopg2.DatabaseError) as error:
        print('Error querying a user: ', error)
        suc = (False, error)
    finally:
        if (conn):
            cur.close()
            conn.close()
        
    return suc



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
        CREATE TABLE dev_%s (
            name VARCHAR(30) NOT NULL,
            dev_id NUMERIC(3) PRIMARY KEY,
            app_key VARCHAR(80),
            description VARCHAR(200)
            FOREIGN KEY (app_key) REFERENCES applications(app_key)
        );
        """
        cur.execute(query, (appkey,))
        conn.commit()
        print('Dev table created')
    except (Exception, psycopg2.DatabaseError) as error:
        print('Error creating app: ', error)
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
    if len(session['name']) > 0:
        apps = get_apps(session['name'].encode('utf-8'))
        print(apps)
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
            res, msg = new_user(username, password)
            if (not res):
                return render_template('signup.html', feedback=msg)
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
            res, msg = chk_user(username, password)
            if (not res):
                return render_template('login.html', feedback=msg)
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
            rer = new_app_devs(request.form['appname'])
            if not res[0] or not rer[0]:
                return render_template('new-app.html', feedback=res[1]+'|'+rer[1])
            else:
                return redirect(url_for('index'))


if __name__ == '__main__':
    server.secret_key = 'sdjfklsjf^$654sd^#sPH'
    server.run(debug = True, host='0.0.0.0')


