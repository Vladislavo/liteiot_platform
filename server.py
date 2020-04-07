from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2

app = Flask(__name__, template_folder='templates/')

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
        cur.execute(query, (name, password))
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


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else: 
        username = request.form['username']
        password = request.form['password']

        if (username == '' or password == ''):
            feedback = 'Username or password fields cannot be empty'
            return render_template('signup.html', feedback=feedback)
        else:
            res, msg = new_user(username, password)
            if (not res):
                return render_template('signup.html', feedback=msg)

            session['name'] = username
        
            return redirect(url_for('index'))

@app.route('/apps')
def apps():
    return '<h1>Manage your apps, ' + app.conf['username'] + '</h1>'

if __name__ == '__main__':
    app.secret_key = 'sdjfklsjf^$654sd^#sPH'
    app.run(debug = True, host='0.0.0.0')
