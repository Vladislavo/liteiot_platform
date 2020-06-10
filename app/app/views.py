from app import app, mail
from flask_mail import Message

from flask import render_template, request, redirect, url_for, session, send_from_directory, flash, after_this_request
import psycopg2

import app.dao.user.user as ud
import app.dao.application.application as ad
import app.dao.device.device as dd
import app.dao.pend.pend as pend
import app.dao.data.data as data
import app.dao.notification.notification as nfs
import app.dao.trigger.trigger as tr
import app.dao.notification_queue.notification_queue as nq
import app.dao.misc.misc as md

import app.helpers.misc as misc
import app.helpers.mailer as mailer
import app.helpers.device_data_model as ddm
import app.helpers.decorators as decorators

import os
import binascii

import logging

MAX_PG = 5
MAX_PG_ENTRIES_USERS = 10
MAX_PG_ENTRIES_DATA = 10
MAX_PG_ENTRIES_GRAPH_HOURS = 24


@app.route('/')
@decorators.restricted('interface')
def index():
    created_apps = ad.get_count_by_user(session['name'])[1][0]
    active_devices = dd.get_count_by_user(session['name'])
    total_activity = md.get_user_data_count(session['name'])[1][0]
    last_activity = md.get_user_data_count_per_day(session['name'])[1][0]
    info = [created_apps, active_devices, total_activity, last_activity]

    return render_template('new/public/dashboard.html', info=info)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if app.config['USERS_SIGNUP']:
        if request.method == 'GET':
            return render_template('new/public/register.html')
        elif request.method == 'POST':
            username = request.form['username']
            password = request.form['password'].encode('utf-8')
            
            if (username == '' or password == ''):
                flash('Username or password fields cannot be empty', 'danger')
                return redirect(request.url)
            elif (len(password) < 8):
                flash('Password length must be at least 8 characters.', 'danger')
                return redirect(request.url)
            else:
                res = ud.create(username, password, 'user')
                if (not res[0]):
                    flash('Error: {}'.format(res[1]), 'danger')
                    return redirect(request.url)
                else:
                    session['name'] = username
                    session['role'] = 'user'

                    app.logger.info('New registered user %s', username)

                    return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('new/public/login.html')
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
                    
                app.logger.info('Logged in user %s', username)
        
                return redirect(url_for('index'))


@app.route('/logout')
def logout():
    app.logger.info('Logged out user %s', session['name'])

    session.clear()
    return redirect(url_for('login'))


@app.route('/applications')
@decorators.restricted('interface')
def applications():
    apps = ad.get_list(session['name'])
   
    return render_template('new/public/applications.html', apps=apps[1])


@app.route('/application/<appkey>')
@decorators.restricted('interface')
@decorators.application_protected
def application(appkey):
    ap = list(ad.get(appkey)[1])
    ap[5] = misc.skey_b64_to_hex(ap[5])
    devs = dd.get_list(ap[1])[1]

    return render_template('new/public/application.html', app=ap, devs=devs)


@app.route('/new-application', methods=['GET', 'POST'])
@decorators.restricted('user')
def application_create():
    if request.method == 'GET':
        return render_template('new/public/new-application.html')
    elif request.method == 'POST':
        if request.form['appname'] == '':
            flash('Application name cannot be empty.', 'danger')
            return redirect(request.url)
        elif request.method == 'POST':
            appkey = misc.rand_str(app.config['APPKEY_LENGTH']).decode('utf-8')
            secure_key = misc.gen_skey_b64(16)
            secure = False

            if request.form.getlist('secure') and request.form.getlist('secure')[0] == 'on':
                secure = True

            res = ad.create(request.form['appname'], appkey, session['name'], request.form['appdesc'], secure, secure_key)
        
            if not res[0]:
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url)
        
            res = dd.create_table_ddm(appkey)
            
            if not res[0]:
                ad.delete(appkey)
                flash('Error: {}'.format(res[1]), 'danger')
                
                app.logger.error('User %s failed to create new application - %s', session['name'], res[1])
                return redirect(request.url)
            else:
                app.logger.info('User %s created new application - %s', session['name'], request.form['appname'])

            return redirect(url_for('applications'))


@app.route('/application/<appkey>/delete')
@decorators.restricted('user')
@decorators.application_protected
def application_delete(appkey):
    devs = dd.get_list(appkey)

    for dev in devs[1]:
        data.delete_table(appkey, dev[1])
        # delete notifications
        nq.delete_per_device(appkey, dev[1])
        nfss = nfs.get_per_device(appkey, dev[1])
        for nf in nfss[1]:
            tr.delete(appkey, dev[1], nf[0])
            tr.delete_function(appkey, dev[1], nf[0])
            nfs.delete(appkey, dev[1], nf[0])

    dd.delete_table(appkey)

    res = ad.delete(appkey)

    if not res[0]:
        flash('Error deleting application: {}'.format(res[1]), 'danger')
        app.logger.error('User %s failed to delete application - %s', session['name'], res[1])
        return redirect(url_for('application', appkey=appkey))
    else:
        app.logger.info('User %s deleted application - %s', session['name'], appkey)
        flash('Application deleted.', 'success')
        return redirect(url_for('applications'))


@app.route('/application/<appkey>/device/<devid>')
@decorators.restricted('interface')
@decorators.application_protected
def application_device(appkey, devid):
    ap = ad.get(appkey)
    if session['name'] == ap[1][2]:
        dev = dd.get(appkey, devid)

        ld = data.get_last_n(appkey, devid, 1)
        cnt = data.get_count(appkey, devid)

        ltup = 'Device have not any sent data yet'

        if ld[0] and ld[1][0] != []:
            ltup = ld[1][0][1]

        return render_template('new/public/device.html', dev=dev[1], app=ap[1], ltup=ltup, total=cnt[1][0], table_max=MAX_PG_ENTRIES_DATA)


@app.route('/application/<appkey>/add-device', methods=['GET', 'POST'])
@decorators.restricted('user')
@decorators.application_protected
def application_add_device(appkey):
    if request.method == 'GET':
        ap = ad.get(appkey)
        dev_list = dd.get_list(appkey)
        return render_template('new/public/add-device.html', app=ap[1], free_ids=misc.prep_id_range(dev_list[1]), models=ddm.MODELS)
    elif request.method == 'POST':
        ddmin = ddm.extract(request)
       
        res = dd.create_ddm(request.form['devname'], request.form['devid'], appkey, request.form['devdesc'], ddmin)
        if not res[0]:
            app.logger.error('User %s failed to add device for application %s - %s', session['name'], appkey, res[1])
            flash('Error: {}'.format(res[1]), 'danger')
            return redirect(request.url)
        else:
            res = data.create_table_ddm(appkey, request.form['devid'])
            if not res[0]:
                app.logger.error('User %s failed to add device for application %s - %s', session['name'], appkey, res[1])
                dd.delete(session['appkey'], request.form['devid'])
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url)
            else:
                app.logger.info('User %s added new device %s for application %s', session['name'], request.form['devname'], appkey)
                flash('Device added', 'success')
                return redirect(url_for('application', appkey=appkey))


@app.route('/application/<appkey>/device/<devid>/delete')
@decorators.restricted('user')
@decorators.application_protected
def application_device_delete(appkey, devid):
    nq.delete_per_device(appkey, devid)
    nfss = nfs.get_per_device(appkey, devid)
    for nf in nfss[1]:
        tr.delete(appkey, devid, nf[0])
        tr.delete_function(appkey, devid, nf[0])
        nfs.delete(appkey, devid, nf[0])

    data.delete_table(appkey, devid)
    res = dd.delete(appkey, devid)

    if not res[0]:
        app.logger.error('User %s failed to delete device %s for application %s - %s', session['name'], devid, appkey, res[1])
        flash('Failed to delete device: {}'.format(res[1]), 'danger')
        redirect(url_for('application_device_settings', appkey=appkey, devid=devid))
    else:
        app.logger.info('User %s deleted for application %s device %s', session['name'], appkey, devid)
        flash('Device removed.', 'success')
        return redirect(url_for('application', appkey=appkey))


@app.route('/application/<appkey>/device/<devid>/configure', methods=['GET', 'POST'])
@decorators.restricted('user')
@decorators.application_protected
def application_device_configuration(appkey, devid):
    if request.method == 'GET':
        pend_msgs = pend.get_list(appkey, devid)
        ap = ad.get(appkey)[1]
        dev = dd.get(appkey, devid)[1]
        if pend_msgs[0]:
            config_list = []

            for pm in pend_msgs[1]:
                cntt = binascii.a2b_base64(pm[2])
                config_id = int(cntt[0])
                config_args = cntt[2:(len(cntt)-1)].decode('utf-8')
                ack = pm[3]
                config_list.append((config_id, config_args, ack, pm[2]))
        
        return render_template('new/public/device-configuration.html', dev=dev, app=ap, config_list=config_list)
    elif request.method == 'POST':
        base64_args = misc.pend_base64_encode(request.form['arg'], request.form['confid'])
        res = pend.create(appkey, devid, base64_args)
        

    if not res[0]:
        app.logger.error('User %s failed to queue config message %s for the app %s device %s - %s', session['name'], base64_args, appkey, devid, res[1])
        flash('Failed to enqueue message: {}'.format(res[1]), 'danger')
        redirect(url_for('application_device_settings', appkey=appkey, devid=devid))
    else:
        app.logger.info('User %s enqueued config message %s for the app %s device %s', session['name'], base64_args, appkey, devid)
        flash('Message enqueued', 'success')
        return '', 201



@app.route('/application/<appkey>/device/<devid>/download-csv')
@decorators.restricted('interface')
@decorators.application_protected
def application_device_download_csv(appkey, devid):
    @after_this_request
    def clean_data_folder(response):
        try:
            filelist = [f for f in os.listdir(app.config['DATA_DOWNLOAD_DIR_OS'])]
            for f in filelist:
                os.remove(app.config['DATA_DOWNLOAD_DIR_OS']+'/'+f)
        except OSError:
            pass
        return response

    dumpd = data.get_all(appkey, devid)
    ap = ad.get(appkey)[1]
    dev = dd.get(appkey, devid)[1]

    fn = ap[0]+ '-' +dev[0]+ '-data.csv'

    with open(app.config['DATA_DOWNLOAD_DIR_OS']+'/'+fn, 'w+') as f: 
        f.write('utc,timestamp,')
        print(dev)
        for d in dev[3]['format']:
            f.write(d)
            f.write(',')
        f.write('\n')
    
        for row in dumpd[1]:
            f.write('{},{},'.format(row[0],row[1]))
            for v in row[2]:
                f.write(str(row[2][v]))
                f.write(',')
            f.write('\n')

    app.logger.info('User %s downloaded data for application %s device %s', session['name'], appkey, devid)

    return send_from_directory(app.config['DATA_DOWNLOAD_DIR'], fn, as_attachment=True)


@app.route('/chart-update')
@decorators.restricted('interface')
def chart_update():
    day_chart_values = md.get_user_data_count_per_hour_period(session['name'], 11)[1]
    day_chart_values = [x[0] for x in day_chart_values]
    day_chart_labels = [misc.local_hour(x) for x in range(11,-1,-1)]
    day_chart = [day_chart_labels, day_chart_values]

    week_chart_values = md.get_user_data_count_per_day_period(session['name'], 6)[1]
    week_chart_values = [x[0] for x in week_chart_values]
    week_chart_labels = [misc.local_weekday(x) for x in range(6,-1,-1)]
    week_chart = [week_chart_labels, week_chart_values]
    
    return "[{}, {}]".format(day_chart, week_chart), 200


@app.route('/recent-activity')
@decorators.restricted('interface')
def recent_activity():
    recent_activity = md.get_recent_activity(session['name'])[1]

    ra = ''
    
    for r in recent_activity:
        dev = dd.get(r[5], r[6])[1]
        ra += '<tr><th scope="row">'+r[1]+'</th><th>'+r[2]+'</th><th>'+r[0]+'</th><th>'+str(ddm.read_data(r[3], dev[3]))+'</th></tr>'

    return ra, 200


@app.route('/application/<appkey>/device/<devid>/remove-configuration')
@decorators.restricted('user')
@decorators.application_protected
def application_device_configuration_remove(appkey, devid):
    res = pend.delete(appkey, devid, request.args.get('conf')+'_')

    if res[0]:
        app.logger.info('User %s deleted config messsage %s for application %s device %s', session['name'], request.args.get('conf'), appkey, devid)
        flash('Configuration message successfully removed.','success')
    else:
        app.logger.error('User %s failed to delet config messsage %s for application %s device %s - %s', session['name'], request.args.get('conf'), appkey, devid, res[1])
        flash('Error removing configuration message: {}'.format(res[1]), 'danger')
    
    return '', 200


@app.route('/application/<appkey>/device/<devid>/variables')
@decorators.restricted('user')
@decorators.application_protected
def application_device_variables(appkey, devid):
    dmodel = dd.get(appkey, devid)
    if dmodel[0]:
        select = '<select class="form-control" id="varname" name="varname" onchange="validate_form();" required>'
        select += '<option value="-">Select Variable</option>'
        for k in dmodel[1][3]['format']:
            select += '<option>'+k+'</option>'
        select += '</select>'
        return select


@app.route('/delete-account')
@decorators.restricted('user')
def delete_account():
    user = ud.get(request.args.get('name'))
    app_list = ad.get_list(user[1][0])

    res = (True,)
    if app_list[0]:
        for app in app_list[1]:
            devs = dd.get_list(app[1])
            for dev in devs[1]:
                res = data.delete_table(app[1], dev[1])
                if not res[0]:
                    break

            if res[0]:
                res = dd.delete_table(app[1])
                
            if res[0]:
                res = ad.delete(app[1])

            if not res[0]:
                break

    if res[0]:
        res = ud.delete(user[1][0])

    if not res[0]:
        app.logger.error('User %s failed to delete the account - %s', session['name'], res[1])
        flash('Error: {}'.format(res[1]), 'danger')
        return render_template('new/public/settings.html', user=session['name'])
    else:
        app.logger.warning('User %s deleted the account', session['name'])
        flash('User {} was successfully deleted'.format(request.args.get('name')), 'success')
        return redirect(url_for('login'))


@app.route('/settings', methods=['GET', 'POST'])
@decorators.restricted('user')
def settings():
    if request.method == 'GET':
        return render_template('new/public/settings.html', user=session['name'])
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

        flash('Settings successfully saved.', 'success')
        return redirect(request.url)


@app.route('/application/<appkey>/device/<devid>/data/<var>/<dest>/<page>')
@decorators.restricted('interface')
@decorators.application_protected
def application_device_data(appkey, devid, var, dest, page):
    dev = dd.get(appkey, devid)[1]
    if dest == 'graph':
        last = data.get_last_hours(appkey, devid, MAX_PG_ENTRIES_GRAPH_HOURS, int(page))
        arr = ''
        if last[0]:
            arr = '['
            last = [ddm.decode_datum(d, dev[3]) for d in last[1]]
            for d in last:
                if var in d[2]:
                    arr += '[new Date('+str(d[0])+'*1000),'+str(d[2][var])+'],'
            arr += ']'
        return arr
    elif dest == 'table':
        # for table <cnt> is in items
        last = data.get_last_range(appkey, devid, [MAX_PG_ENTRIES_DATA, (int(page)-1)*MAX_PG_ENTRIES_DATA])
        t = ''
        if last[0]:
            last = [ddm.decode_datum(d, dev[3]) for d in last[1]]
            for d in last:
                if var in d[2]:
                    t += '<tr><th>'+d[1]+'</th><th>'+str(d[2][var])+'</th></tr>'
        return t


@app.route('/application/<appkey>/alerts')
@decorators.restricted('interface')
@decorators.application_protected
def application_alerts(appkey):
    ap = ad.get(appkey)
    alerts = nfs.get_alerts_list(appkey)
    return render_template('new/public/alerts.html', alert_list=alerts[1], app=ap[1])


@app.route('/application/<appkey>/new-alert', methods=['GET', 'POST'])
@decorators.restricted('user')
@decorators.application_protected
def application_new_alert(appkey):
    if request.method == 'GET':
        ap = ad.get(appkey)
        devs = dd.get_list(appkey)
        
        return render_template('new/public/new-alert.html', devs=devs[1], app=ap[1])
    elif request.method == 'POST':
        # create new notification
        nid = misc.rand_str(app.config['NID_LENGTH']).decode('utf-8')
        dev = dd.get(appkey, request.form['devid'])
        
        try:
            desc = dev[1][0]+'.'+request.form['varname']+' '+request.form['operation']+' '+request.form['avalue']
            res = nfs.create(nid, appkey, request.form['devid'], request.form['alertname'], desc, 'alert', request.form['alertemail'])
            if res[0]:
                # create new function and trigger
                t = tr.create_function_rt(appkey, request.form['devid'], nid, [request.form['varname'],request.form['operation'],request.form['avalue']],'alert',request.form['alertemail'])
                t = tr.create(appkey, request.form['devid'], nid)
                flash('Alert created', 'success')
                app.logger.info('User %s created alert %s - %s for application %s', session['name'], nid, desc, appkey)
                return redirect(url_for('application_alerts', appkey=appkey))
            else:
                app.logger.error('User %s failed to create alert for application %s - %s', session['name'], appkey, res[1])
                flash('Error creating new alert: {}'.format(res[1]), 'danger')
                return redirect(request.url) 
        except Exception as e:
            app.logger.error('User %s failed to create alert for application %s - %s', session['name'], appkey, e)
            flash('Error creating new alert: {}. Make sure you have filled all form fields.'.format(e), 'danger')
            return redirect(request.url) 


@app.route('/application/<appkey>/delete-<ntype>')
@decorators.restricted('user')
@decorators.application_protected
def application_notification_remove(appkey, ntype):
    nq.delete(appkey, request.args.get('devid'), request.args.get('id'))
    tr.delete(appkey, request.args.get('devid'), request.args.get('id'))
    tr.delete_function(appkey, request.args.get('devid'), request.args.get('id'))
    res = nfs.delete(appkey, request.args.get('devid'), request.args.get('id'))

    if res[0]:
        app.logger.info('User %s deleted %s %s for application %s', session['name'], ntype, request.args.get('id'), appkey)
        flash('{} removed'.format(ntype.capitalize()), 'success')
        return '', 200
    else:
        app.logger.error('User %s failed to delete %s %s for application %s - %s', session['name'], ntype, request.args.get('id'), appkey, res[1])
        flash('{} cannot be removed : {}'.format(ntype.capitalize(), res[1]), 'danger')
        return '', 500


@app.route('/application/<appkey>/automation')
@decorators.restricted('interface')
@decorators.application_protected
def application_automation(appkey):
    ap = ad.get(appkey)
    ats = nfs.get_automation_list(appkey)
    
    return render_template('new/public/automation.html', automations=ats[1], app=ap[1])


@app.route('/application/<appkey>/new-automation', methods=['GET', 'POST'])
@decorators.restricted('user')
@decorators.application_protected
def application_new_automation(appkey):
    if request.method == 'GET':
        ap = ad.get(appkey)
        devs = dd.get_list(appkey)
        
        return render_template('new/public/new-automation.html', devs=devs[1], app=ap[1])
    elif request.method == 'POST':
        # create new notification
        nid = misc.rand_str(app.config['NID_LENGTH']).decode('utf-8')
        dev = dd.get(appkey, request.form['devid'])
        adev = dd.get(appkey, request.form['adevid'])
        
        try:
            desc = 'IF '+dev[1][0]+'.'+request.form['varname']+' '+request.form['operation']+' '+request.form['avalue']+' THEN '+adev[1][0]+'.confID_'+request.form['confid']+' = '+request.form['arg']
            # action format: '<devid>#<confid>#<arg>'
            action = request.form['adevid']+'#'+request.form['confid']+'#'+request.form['arg']
            res = nfs.create(nid, appkey, request.form['devid'], request.form['automationname'], desc, 'automation', action)
            if res[0]:
                # create new function and trigger
                t = tr.create_function_rt(appkey, request.form['devid'], nid, [request.form['varname'],request.form['operation'],request.form['avalue']],'automation', action)
                tr.create(appkey, request.form['devid'], nid)
                app.logger.info('User %s created automation %s - %s for application %s', session['name'], nid, desc, appkey)
                flash('Automation created', 'success')
                return redirect(url_for('application_automation', appkey=appkey))
            else:
                app.logger.error('User %s failed to create automation for application %s - %s', session['name'], appkey, res[1])
                flash('Error creating new alert: {}'.format(res[1]), 'danger')
                return redirect(request.url) 
        except Exception as e:
            app.logger.error('User %s failed to create automation for application %s - %s', session['name'], appkey, e)
            flash('Error creating new alert: {}. Make sure you have filled all form fields.'.format(e), 'danger')
            return redirect(request.url) 


@app.route('/application/<appkey>/settings', methods=['GET', 'POST'])
@decorators.restricted('user')
@decorators.application_protected
def application_settings(appkey):
    if request.method == 'GET':
        ap = ad.get(appkey)

        return render_template('new/public/application-settings.html', app=ap[1])
    elif request.method == 'POST':
        if request.form.getlist('secure') and request.form.getlist('secure')[0] == 'on':
            secure = True
        else:
            secure = False
        
        res = ad.update(appkey, request.form['appname'], request.form['appdesc'], secure)
    
        if not res[0]:
            flash('Error: {}'.format(res[1]), 'danger')
            return redirect(request.url)
    
        return redirect(request.url)


@app.route('/application/<appkey>/device/<devid>/settings', methods=['GET', 'POST'])
@decorators.restricted('user')
@decorators.application_protected
def application_device_settings(appkey, devid):
    if request.method == 'GET':
        ap = ad.get(appkey)
        dev = dd.get(appkey, devid)

        return render_template('new/public/device-settings.html', app=ap[1], dev=dev[1], models=ddm.MODELS)
    elif request.method == 'POST':
        ddmin = ddm.extract(request)
        res = dd.update_ddm(appkey, devid, request.form['devname'], request.form['devdesc'], ddmin)
        
        if not res[0]:
            flash('Error: {}'.format(res[1]), 'danger')
            return redirect(request.url)
    
        return redirect(request.url)



def pend_delete_all_ack():
    pend.delete_all_ack()

def fire_notifications(app):
    fnfs = nq.get_all()
    if fnfs[0]:
        for fnf in fnfs[1]:
            nf = nfs.get(fnf[1], fnf[2], fnf[0])
            if nf[1][5] == 'alert':
                # send mail
                mailer.send_mail(app, nf[1], fnf)
            elif nf[1][5] == 'automation':
                # enqueue confid
                # action format: '<devid>#<confid>#<arg>'
                action = nf[1][6].split('#')
                base64_args = misc.pend_base64_encode(action[2], action[1])
                pend.create(nf[1][1], action[0], base64_args)
            nq.delete(fnf[1], fnf[2], fnf[0])
