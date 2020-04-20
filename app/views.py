from app import app

from flask import render_template, request, redirect, url_for, session, send_from_directory, flash
import psycopg2

import app.dao.user.user as ud
import app.dao.application.application as ad
import app.dao.device.device as dd
import app.dao.pend.pend as pend
import app.dao.data.data as data

import app.helpers.misc as misc

import os


@app.route('/')
def index():
    if 'name' in session and len(session['name']) > 0:
        apps = ad.get_list(session['name'])
        
        session.pop('appkey', None)
        # print('apps: ', apps)
        if apps[0]:
            return render_template('public/index.html', apps=apps[1])
        else:
            return render_template('public/index.html', feedback=apps[1])
    else:
        return render_template('public/index.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('public/signup.html')
    else: 
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        if (username == '' or password == ''):
            feedback = 'Username or password fields cannot be empty'
            return render_template('public/signup.html', feedback=feedback)
        elif (len(password) < 8):
            flash('Password length must be at least 8 characters.', 'danger')
            return redirect(request.url)
        else:
            res = ud.create(username, password)
            if (not res[0]):
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url)
            else:
                session['name'] = username
                
                flash('User successfully created.', 'success')
                return redirect(url_for('index'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('public/login.html')
    else: 
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        if (username == '' or password == ''):
            flash('Username or password fields cannot be empty', 'danger')
            return redirect(request.url)
        else:
            res = ud.get(username, password)
            if (not res[0]):
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url)
            else:
                session['name'] = username
        
                return redirect(url_for('index'))



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))



@app.route('/new-app')
def new_application():
    if 'name' in session:
        return render_template('public/new-app.html')
    else:
        return redirect(url_for('index'))



@app.route('/app', methods=['GET', 'POST'])
def app_():
    if 'name' in session:
        if request.method == 'GET':
            
            session['appkey'] = request.args.get('appkey')

            ap = ad.get(session['appkey'])
            devs = dd.get_list(ap[1][1])
        
            try:
                filelist = [f for f in os.listdir(app.config['DATA_DOWNLOAD_DIR']) if f.startswith(session['appkey'])]
                for f in filelist:
                    os.remove(app.config['DATA_DOWNLOAD_DIR']+'/'+f)
            except OSError:
                pass

           # print('devs : ', devs)
            return render_template('public/app.html', app=ap[1], devs=devs[1])
        else:
            if request.form['appname'] == '':
                error = 'Application name cannot be empty.'
                return render_template('public/new-app.html', feedback=error)
            else:
                appkey = misc.rand_str(app.config['APPKEY_LENGTH'])
                res = ad.create(request.form['appname'], appkey, session['name'], request.form['appdesc'])
            
                if not res[0]:
                    return render_template('public/new-app.html', feedback=res[1])
            
                res = dd.create_table(appkey)
            
                if not res[0]:
                    ad.delete(appkey)
                    return render_template('public/new-app.html', feedback=res[1])
            
                return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/delete-app')
def delete_app():
    if 'name' in session:
        devs = dd.get_list(session['appkey'])
    
        for dev in devs[1]:
            data.delete_table(session['appkey'], dev[1])
    
        dd.delete_table(session['appkey'])
    
        res = ad.delete(session['appkey'])
    
        if not res[0]:
            return redirect(url_for('app_'))
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


@app.route('/add-dev')
def new_dev():
    if 'name' in session:
        dev_list = dd.get_list(session['appkey'])
    
    #print('dev list : ', dev_list)

        if not dev_list[0]:
            return render_template('public/add-dev.html', feedback=dev_list[1])
        else:
            return render_template('public/add-dev.html', free_ids=misc.prep_id_range(dev_list[1]))
    else:
        return redirect(url_for('index'))
 


@app.route('/dev', methods=['GET', 'POST'])
def dev():
    if 'name' in session:
        if request.method == 'GET':
            dev = dd.get(session['appkey'], request.args.get('id'))

            session['devid'] = int(dev[1][1])
            session['devname'] = dev[1][0]
        
            last = data.get_last_n(session['appkey'], session['devid'], 1)
        
            ltup = 'Device have not sent data yet'

            if last[0]:
                ltup = last[1][0][1]

            return render_template('public/dev.html', dev=dev[1], appkey=session['appkey'], ltup=ltup)
        else:
            res = dd.create(request.form['devname'], request.form['devid'], session['appkey'], request.form['devdesc'])

            if not res[0]:
                return render_template('public/add-dev.html', feedback=res[1])
            else:
                res = data.create_table(session['appkey'], request.form['devid'])
            
                if not res[0]:
                    dd.delete(session['appkey'], request.form['devid'])
                    return render_template('public/add-dev.html', feedback=res[1])
                else:
                    return redirect(url_for('app', appkey=session['appkey']))
    else:
        return redirect(url_for('index'))


@app.route('/dev-conf', methods=['GET', 'POST'])
def dev_conf():
    if 'name' in session and 'devid' in session:
        if request.method == 'GET':
            return render_template('public/dev-conf.html', devname=session['devname'])
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
    else:
        return redirect(url_for('index'))


@app.route('/delete-dev')
def delete_dev():
    if 'name' in session and 'devid' in session:
        data.delete_table(session['appkey'], session['devid'])
        res = dd.delete(session['appkey'], session['devid'])

        return redirect(url_for('app_', appkey=session['appkey']))
    else:
        return redirect(utl_for('index'))


@app.route('/dev-data')
def dev_data():
    if 'name' in session and 'devid' in session:
        last = data.get_last_n(session['appkey'], session['devid'], 10)  
        count = data.get_count(session['appkey'], session['devid'])

        last_ctr = 10
        if count[1][0] < 10:
            last_ctr = count[1][0]

        #print(last[1][2][2])
        #print(type(last[1][2][2]))
        #print(count)
        if count[1][0] > 0:
            return render_template('public/dev-data.html', data=last[1], total=count[1][0], lastctr=last_ctr, devname=session['devname'])
        else:
            return render_template('public/dev-data.html', devname=session['devname'])
    else:
        return redirect(utl_for('index'))

@app.route('/data-csv')
def data_csv():
    if 'name' in session and 'devid' in session:
        dumpd = data.get_all(session['appkey'], session['devid'])

        fn = session['appkey']+ '_' +str(session['devid'])+ '.csv'

        with open(app.config['DATA_DOWNLOAD_DIR']+'/'+fn, 'w') as f: 
            for d in dumpd[1][0][2]:
                f.write(d)
                f.write(',')
            f.write('\n')
        
            for row in dumpd[1]:
                for v in row[2]:
                    f.write(str(row[2][v]))
                    f.write(',')
                f.write('\n')
    
        return send_from_directory(app.config['DATA_DOWNLOAD_DIR'], fn, as_attachment=True)
    else:
        return redirect(utl_for('index'))
