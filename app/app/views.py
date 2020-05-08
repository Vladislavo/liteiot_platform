from app import app

from flask import render_template, request, redirect, url_for, session, send_from_directory, flash
import psycopg2

import app.dao.user.user as ud
import app.dao.application.application as ad
import app.dao.device.device as dd
import app.dao.pend.pend as pend
import app.dao.data.data as data

import app.helpers.misc as misc

import binascii
import os


MAX_PG = 5
MAX_PG_ENTRIES_USERS = 10
MAX_PG_ENTRIES_DATA = 10
MAX_PG_ENTRIES_GRAPH_HOURS = 24


@app.route('/')
def index():
    if 'name' in session and len(session['name']) > 0:
        apps = ad.get_list(session['name'])
        
        session.pop('appkey', None)
        # print('apps: ', apps)
        if apps[0]:
            return render_template('public/index.html', apps=apps[1], users_signup=app.config['USERS_SIGNUP'])
        else:
            return render_template('public/index.html', feedback=apps[1], users_signup=app.config['USERS_SIGNUP'])
    else:
        return render_template('public/index.html', users_signup=app.config['USERS_SIGNUP'])



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        if session['role'] and session['role'] == 'admin':
            return render_template('admin/signup.html', users_signup=app.config['USERS_SIGNUP'])
        else:
            if app.config['USERS_SIGNUP']:
                return render_template('public/signup.html', users_signup=app.config['USERS_SIGNUP'])
            else:
                return redirect(url_for('index', users_signup=app.config['USERS_SIGNUP']))
    else:
        if app.config['USERS_SIGNUP'] or session['role'] == 'admin':
            username = request.form['username']
            password = request.form['password'].encode('utf-8')
            
            if (username == '' or password == ''):
                feedback = 'Username or password fields cannot be empty'
                return render_template('public/signup.html', feedback=feedback, users_signup=app.config['USERS_SIGNUP'])
            elif (len(password) < 8):
                flash('Password length must be at least 8 characters.', 'danger')
                return redirect(request.url, users_signup=app.config['USERS_SIGNUP'])
            else:
                role = 'user'
                if request.form['role'] and request.form['role'] == 'administrator':
                    role = 'admin'

                res = ud.create(username, password, role)
                if (not res[0]):
                    flash('Error: {}'.format(res[1]), 'danger')
                    return redirect(request.url)
                else:
                    session['name'] = username
                    
                    flash('User successfully created.', 'success')

                    if session['role'] and session['role'] == 'admin':
                        return redirect(url_for('dashboard'))
                    else:
                        return redirect(url_for('index'))
        else:
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
            res = ud.check(username, password)
            if (not res[0]):
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url)
            else:
                session['name'] = username
                session['role'] = res[1][2]
        
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
            
            if session['role'] == 'admin' or session['name'] == ap[1][2]:
                return render_template('public/app.html', app=ap[1], devs=devs[1])
            else:
                return redirect(url_for('index'))
        else:
            if request.form['appname'] == '':
                error = 'Application name cannot be empty.'
                return render_template('public/new-app.html', feedback=error)
            else:
                appkey = misc.rand_str(app.config['APPKEY_LENGTH']).decode('utf-8')
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
            ap = ad.get(session['appkey'])
            if session['role'] == 'admin' or session['name'] == ap[1][2]:
                dev = dd.get(session['appkey'], request.args.get('id'))

                session['devid'] = int(dev[1][1])
                session['devname'] = dev[1][0]
        
                last = data.get_last_n(session['appkey'], session['devid'], 1)
        
                ltup = 'Device have not sent data yet'

                if last[0]:
                    ltup = last[1][0][1]

                return render_template('public/dev.html', dev=dev[1], appkey=session['appkey'], ltup=ltup)
            else:
                return redirect(url_for('index'))
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
                    return redirect(url_for('app_', appkey=session['appkey']))
    else:
        return redirect(url_for('index'))


@app.route('/dev-conf', methods=['GET', 'POST'])
def dev_conf():
    if 'name' in session and 'devid' in session:
        if request.method == 'GET':
            pend_msgs = pend.get_list(session['appkey'], session['devid'])
            
            if pend_msgs[0]:
                config_list = []

                for pm in pend_msgs[1]:
                    cntt = binascii.a2b_base64(pm[2])
                    config_id = int(cntt[0])
                    config_args = cntt[2:(len(cntt)-1)].decode('utf-8')
                    ack = pm[3]
                    config_list.append((config_id, config_args, ack, pm[2]))

                return render_template('public/dev-conf.html', devname=session['devname'], config_list=config_list)
            else:
                return render_template('public/dev-conf.html', devname=session['devname'])
        else:
            argslen = len(request.form['arg']) + 1
            args = bytearray(argslen + 2)
            args[0] = int(request.form['confid'])
            args[1] = argslen
        
            bstr = bytes(request.form['arg'].encode('utf-8'))
            i = 0
            while i < argslen - 1:
                args[2+i] = bstr[i]
                i += 1

            base64_args = binascii.b2a_base64(args).decode('utf-8')

            pend.create(session['appkey'], session['devid'], base64_args)

            return redirect(url_for('dev', id=session['devid']))
    else:
        return redirect(url_for('index'))

@app.route('/dev-conf-rm')
def dev_conf_rm():
    if 'name' in session and 'appkey' in session and 'devid' in session:
        res = pend.delete(session['appkey'], session['devid'], request.args.get('conf')+'_')

        if res[0]:
            flash('Configuration message successfully removed.','success')
            return redirect(url_for('dev_conf'))
        else:
            flash('Error removing configuration message: {}'.format(res[1]), 'danger')
            return redirect(url_for('dev_conf'))
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
def dev_data_pg():
    if 'name' in session and 'devid' in session:
        cur_pg = 1
        if request.args.get('p'):
            cur_pg = int(request.args.get('p'))
            if cur_pg < 1:
                cur_pg = 1
        
        last = data.get_last_range(session['appkey'], session['devid'], [MAX_PG_ENTRIES_DATA, (cur_pg-1)*MAX_PG_ENTRIES_DATA])
        
        ent_cnt = data.get_count(session['appkey'], session['devid'])
        if ent_cnt[0]:
            # range data
            rd = misc.paging(cur_pg, ent_cnt[1][0], MAX_PG_ENTRIES_DATA, MAX_PG)

            if ent_cnt[1][0] > 0:
                return render_template('public/dev-data-t.html', data=last[1], total=ent_cnt[1][0], cp=cur_pg, np=rd[2], pp=rd[0], pr=rd[1], devname=session['devname'])
            else:
                return render_template('public/dev-data-t.html', devname=session['devname'])
        else:
            flash('Error: {}'.format(ent_cnt[1]), 'danger')
            return render_template('public/dev-data-t.html', devname=session['devname'])
    else:
        return redirect(utl_for('index'))



@app.route('/data-csv')
def data_csv():
    if 'name' in session and 'devid' in session:
        dumpd = data.get_all(session['appkey'], session['devid'])

        fn = session['appkey']+ '_' +str(session['devid'])+ '.csv'

        with open(app.config['DATA_DOWNLOAD_DIR_OS']+'/'+fn, 'w+') as f: 
            f.write('utc,timestamp,')
            for d in dumpd[1][0][2]:
                f.write(d)
                f.write(',')
            f.write('\n')
        
            for row in dumpd[1]:
                f.write('{},{},'.format(row[0],row[1]))
                for v in row[2]:
                    f.write(str(row[2][v]))
                    f.write(',')
                f.write('\n')
    
        return send_from_directory(app.config['DATA_DOWNLOAD_DIR'], fn, as_attachment=True)
    else:
        return redirect(utl_for('index'))


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'role' in session and session['role'] == 'admin':
        user_cnt = ud.get_count()
        apps_cnt = ad.get_count()
        devs_cnt = dd.get_count_all()

        cur_pg = 1
        if request.args.get('p'):
            cur_pg = int(request.args.get('p'))
            if cur_pg < 1:
                cur_pg = 1

        users = None
        
        if request.method == 'POST':
            session['users_filter'] = request.form['username']
            
        if 'users_filter' in session:
            users = ud.get_range_name(session['users_filter'], [MAX_PG_ENTRIES_USERS, (cur_pg-1)*MAX_PG_ENTRIES_USERS])
            print(users)
            rd = misc.paging(cur_pg, len(users[1]), MAX_PG_ENTRIES_USERS, MAX_PG)
        else:
            users = ud.get_range([MAX_PG_ENTRIES_USERS, (cur_pg-1)*MAX_PG_ENTRIES_USERS])
            rd = misc.paging(cur_pg, user_cnt[1][0], MAX_PG_ENTRIES_USERS, MAX_PG)
        
        return render_template('admin/dashboard.html', users_cnt=user_cnt[1][0], apps_cnt=apps_cnt[1][0], dev_cnt=devs_cnt, users=users[1], pp=rd[0], pr=rd[1], np=rd[2], cp=cur_pg, usn=(cur_pg-1)*MAX_PG_ENTRIES_USERS+1)
    else:
        return redirect(url_for('index'))


@app.route('/dashboard-clean-search')
def dashboard_clean_search():
    if 'users_filter' in session:
        session.pop('users_filter', None)
    return redirect(url_for('dashboard'))


@app.route('/user')
def user():
    if 'role' in session and session['role'] == 'admin':
        name = request.args.get('name')
        apps = ad.get_list(name)
        
        session.pop('appkey', None)
        # print('apps: ', apps)
        if apps[0]:
            return render_template('admin/user.html', apps=apps[1], username=name)
        else:
            return render_template('admin/user.html', feedback=apps[1], username=name)
    else:
        return render_template('public/index.html')


@app.route('/user-delete')
def user_delete():
    user = ud.get(request.args.get('name'))
    if user[0] and user[1][2] != 'admin' and session['role'] == 'admin':
        app_list = ad.get_list(user[1][0])

        res = (True,)
        if app_list[0]:
            for app in app_list[1]:
                devs = dd.get_list(app[1])
                print('devs: {}'.format(devs))
                for dev in devs[1]:
                    res = data.delete_table(app[1], dev[1])
                    print ('data del {}'.format(res))
                    if not res[0]:
                        break
    
                if res[0]:
                    res = dd.delete_table(app[1])
                    print ('devices del {}'.format(res))
                    
                if res[0]:
                    res = ad.delete(app[1])
                    print ('app del {}'.format(res))

                if not res[0]:
                    break

        if res[0]:
            res = ud.delete(user[1][0])
            print ('user del {}'.format(res))

        if not res[0]:
            flash('Error: {}'.format(res[1]), 'danger')
            return render_template('admin/user.html', username=user[1][0])
        else:
                return redirect(url_for('dashboard'))
    else:
        flash('Warning: the user is admin or does not exist.' ,'warning')
        return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        if session['role'] == 'admin':
            return render_template('admin/settings.html', username=session['name'], users_signup=app.config['USERS_SIGNUP'])
        else:
            return render_template('public/settings.html', username=session['name'])
    else:
        if request.form['name'] != session['name']:
            res = ud.update_name(session['name'], request.form['name'])
            if not res[0]:
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url);
            else:
                session['name'] = request.form['name']
        if request.form['password'] != '':
            res = ud.update_password(session['name'], request.form['password'].encode('utf-8'))
            if not res[0]:
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url)
        if session['role'] == 'admin':
            if request.form.getlist('users_signup') and request.form.getlist('users_signup')[0] == 'us':
                app.config['USERS_SIGNUP'] = True
            else:
                app.config['USERS_SIGNUP'] = False


        return redirect(request.url)


@app.route('/dev-data/<var>/<dest>/<page>')
def dev_data(var, dest, page):
    if dest == 'graph':
        last = data.get_last_hours(session['appkey'], session['devid'], MAX_PG_ENTRIES_GRAPH_HOURS, int(page))
        arr = '[["Time", "{}"],'.format(var)
        if last[0]:
            for d in last[1]:
                arr += '[new Date('+str(d[0])+'*1000),'+str(d[2][var])+'],'
            arr += ']'
        return arr
    elif dest == 'table':
        # for table <cnt> is in items
        last = data.get_last_range(session['appkey'], session['devid'], [MAX_PG_ENTRIES_DATA, (int(page)-1)*MAX_PG_ENTRIES_DATA])
        t = """ <thead>
                    <th>Time</th>
                    <th>{}</th>
                </thead>
                <tbody>
        """.format(var)
        if last[0]:
            for d in last[1]:
                t += '<tr><th>'+d[1]+'</th><th>'+str(d[2][var])+'</th></tr>'
        t += '</tbody>'
        return t


def pend_delete_all_ack():
    pend.delete_all_ack()
