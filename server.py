from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import bcrypt
import misc
import dao.user.user as ud
import dao.application.application as ad
import dao.device.device as dd


server = Flask(__name__, template_folder='templates/')


def prep_ids(dev_list):
    return "any"

@server.route('/')
def index():
    if 'name' in session and len(session['name']) > 0:
        ah = ad.ApplicationDao()
        apps = ah.get_list(session['name'].encode('utf-8'))

        session.pop('appkey', None)
        print('apps: ', apps)
        if apps[0]:
            return render_template('index.html', apps=apps[1])
        else:
            return render_template('index.html', feedback=apps[1])



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
    ah = ad.ApplicationDao()
    if request.method == 'GET':
        dh = dd.DeviceDao()
        appkey = None
        if 'appkey' in session:
            appkey = session['appkey']
        else:
            appkey = request.args.get('appkey')
            session['appkey'] = request.args.get('appkey')

        app = ah.get(appkey)
        devs = dh.get_list(app[1][1])
        
        print('devs : ', devs)
        return render_template('app.html', app=app[1], devs=devs[1])
    else:
        if request.form['appname'] == '':
            error = 'Application name cannot be empty.'
            return render_template('new-app.html', feedback=error)
        else:
            res = ah.create(request.form['appname'], session['name'], request.form['appdesc'])
            
            if not res[0]:
                return render_template('new-app.html', feedback=res[1])

            #res = new_app_devs(request.form['appname'])
            #if not res[0]:
            #    rm_app(request.form['appname'])
            #    return render_template('new-app.html', feedback=res[1])
            
            #if not res[0] or not rer[0]:
            #    return render_template('new-app.html', feedback=str(res[1])+'|'+str(rer[1]))
            #else:
            return redirect(url_for('index'))


@server.route('/add-dev')
def new_dev():
    free_ids = 'whatever'
    
    dh = dd.DeviceDao()
    dev_list = dh.get_list(session['appkey'])
    
    print('dev list : ', dev_list)

    if not dev_list[0]:
        return render_template('add-dev.html', feedback=dev_list[1])
    else:
        return render_template('add-dev.html', free_ids=prep_ids(dev_list[1]))
 


@server.route('/dev', methods=['GET', 'POST'])
def dev():
    dh = dd.DeviceDao()
    if request.method == 'GET':
        dev = dh.get(session['appkey'], request.args.get('dev_id'))
        ltup = 'recently'

        return render_template('dev.html', dev=dev[1], ltup=ltup)
    else:
        res = dh.create(request.form['devname'], request.form['devid'], session['appkey'], request.form['devdesc'])
        
        if not res[0]:
            return render_template('add-dev.html', feedback=res[1])
        else:
            return redirect(url_for('app'))


if __name__ == '__main__':
    server.secret_key = 'sdjfklsjf^$654sd^#sPH'
    server.run(debug = True, host='0.0.0.0')


