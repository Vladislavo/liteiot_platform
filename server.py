from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import psycopg2
import bcrypt
import misc
import dao.user.user as ud
import dao.application.application as ad
import dao.device.device as dd
import dao.pend.pend as pend
import dao.data.data as data
import binascii


APP_KEY_LEN = 8
DATA_DOWNLOAD_DIR = 'data'

server = Flask(__name__, template_folder='templates/')

@server.route('/')
def index():
    if 'name' in session and len(session['name']) > 0:
        ah = ad.ApplicationDao()
        apps = ah.get_list(session['name'].encode('utf-8'))

        session.pop('appkey', None)
        # print('apps: ', apps)
        if apps[0]:
            return render_template('index.html', apps=apps[1])
        else:
            return render_template('index.html', feedback=apps[1])
    else:
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
    ah = ad.ApplicationDao()
    if request.method == 'GET':
        dh = dd.DeviceDao()
            
        session['appkey'] = request.args.get('appkey')

        app = ah.get(session['appkey'])
        devs = dh.get_list(app[1][1])
        
        # print('devs : ', devs)
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
        data.delete_table(session['appkey'], dev[1])
    
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
    
    #print('dev list : ', dev_list)

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
            res = data.create_table(session['appkey'], request.form['devid'])
            
            if not res[0]:
                dh.delete(session['appkey'], request.form['devid'])
                return render_template('add-dev.html', feedback=res[1])
            else:
                return redirect(url_for('app', appkey=session['appkey']))


@server.route('/dev-conf', methods=['GET', 'POST'])
def dev_conf():
    if request.method == 'GET':
        return render_template('dev-conf.html', devname=session['devname'])
    else:
        
        argslen = len(request.form['arg']) + 1
        args = bytearray(argslen + 2)
        args[0] = int(request.form['confid'])
        args[1] = argslen
        
        bstr = bytes(request.form['arg'])
        i = 0
        while i < argslen - 1:
            args[2+i] = bstr[i]
            i += 1

        base64_args = binascii.b2a_base64(args).decode('utf-8')

        pend.create(session['appkey'], session['devid'], base64_args)

        #print('msg = ', args)
        #print('base64 = ', base64_args)
        #print(type(request.form['arg'].encode('utf-8')))
        #print(request.form['arg'].encode('utf-8'))
        
        return redirect(url_for('dev', id=session['devid']))


@server.route('/delete-dev')
def delete_dev():
    dh = dd.DeviceDao()
    data.delete_table(session['appkey'], session['devid'])
    res = dh.delete(session['appkey'], session['devid'])

    return redirect(url_for('app', appkey=session['appkey']))


@server.route('/dev-data')
def dev_data():
    last = data.get_last_n(session['appkey'], session['devid'], 5)  
    count = data.get_count(session['appkey'], session['devid'])

    #print(last)
    #print(count)
    if count[1][0] > 0:
        return render_template('dev-data.html', data=last[1], total=count[1][0])
    else:
        return render_template('dev-data.html')

@server.route('/data-csv')
def data_csv():
    dumpd = data.get_all(session['appkey'], session['devid'])

    fn = session['appkey']+ '_' +str(session['devid'])+ '.csv'

    with open(DATA_DOWNLOAD_DIR+'/'+fn, 'w') as f: 
        for d in dumpd[1][0][2]:
            f.write(d)
            f.write(',')
        f.write('\n')
        
        for row in dumpd[1]:
            for v in row[2]:
                f.write(str(row[2][v]))
                f.write(',')
            f.write('\n')
    
    return send_from_directory(DATA_DOWNLOAD_DIR, fn, as_attachment=True)
        

if __name__ == '__main__':
    server.secret_key = 'sdjfklsjf^$654sd^#sPH'
    server.run(debug = True, host='0.0.0.0')


