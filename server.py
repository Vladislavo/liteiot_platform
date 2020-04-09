from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import bcrypt
import misc
import dao.user.user as ud
import dao.application.application as ad
import dao.device.device as dd

APP_KEY_LEN = 8

server = Flask(__name__, template_folder='templates/')

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
            
        session['appkey'] = request.args.get('appkey')

        app = ah.get(session['appkey'])
        devs = dh.get_list(app[1][1])
        
        print('devs : ', devs)
        return render_template('app.html', app=app[1], devs=devs[1])
    else:
        if request.form['appname'] == '':
            error = 'Application name cannot be empty.'
            return render_template('new-app.html', feedback=error)
        else:
            appkey = misc.rand_str(APP_KEY_LEN)
            res = ah.create(request.form['appname'], appkey, session['name'], request.form['appdesc'])
            
            if not res[0]:
                return render_template('new-app.html', feedback=res[1])
            
            dh = dd.DeviceDao()
            res = dh.create_table(appkey)
            
            if not res[0]:
                ah.delete(appkey)
                return render_template('new-app.html', feedback=res[1])
            
            return redirect(url_for('index'))

@server.route('/delete-app')
def delete_app():
    dh = dd.DeviceDao()
    devs = dh.get_list(session['appkey'])
    
    for dev in devs[1]:
        dh.delete_datatable(session['appkey'], dev[1])
    
    dh.delete_table(session['appkey'])
    
    ah = ad.ApplicationDao()
    res = ah.delete(session['appkey'])
    
    if not res[0]:
        return redirect(url_for('app'))
    else:
        return redirect(url_for('index'))

@server.route('/add-dev')
def new_dev():
    dh = dd.DeviceDao()
    dev_list = dh.get_list(session['appkey'])
    
    print('dev list : ', dev_list)

    if not dev_list[0]:
        return render_template('add-dev.html', feedback=dev_list[1])
    else:
        return render_template('add-dev.html', free_ids=misc.prep_id_range(dev_list[1]))
 


@server.route('/dev', methods=['GET', 'POST'])
def dev():
    dh = dd.DeviceDao()
    if request.method == 'GET':
        dev = dh.get(session['appkey'], request.args.get('id'))
        ltup = 'recently'

        session['devid'] = dev[1][1]
        session['devname'] = dev[1][0]

        return render_template('dev.html', dev=dev[1], appkey=session['appkey'], ltup=ltup)
    else:
        res = dh.create(request.form['devname'], request.form['devid'], session['appkey'], request.form['devdesc'])

        if not res[0]:
            return render_template('add-dev.html', feedback=res[1])
        else:
            res = dh.create_datatable(session['appkey'], request.form['devid'])
            
            if not res[0]:
                dh.delete(session['appkey'], request.form['devid'])
                return render_template('add-dev.html', feedback=res[1])
            else:
                return redirect(url_for('app'))


@server.route('/dev-conf', methods=['GET', 'POST'])
def dev_conf():
    if request.method == 'GET':
        return render_template('dev-conf.html', devname=session['devname'])
    else:
        pass

@server.route('/delete-dev')
def delete_dev():
    dh = dd.DeviceDao()
    dh.delete_datatable(session['appkey'], request.args.get('id'))
    res = dh.delete(session['appkey'], request.args.get('id'))

    return redirect(url_for('app', appkey=session['appkey']))


if __name__ == '__main__':
    server.secret_key = 'sdjfklsjf^$654sd^#sPH'
    server.run(debug = True, host='0.0.0.0')


