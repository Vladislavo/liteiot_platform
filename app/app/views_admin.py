from app import app

from flask import render_template, request, redirect, url_for, session, flash, after_this_request, send_from_directory

import app.dao.user.user as ud
import app.dao.application.application as ad
import app.dao.device.device as dd
import app.dao.pend.pend as pend
import app.dao.data.data as data
import app.dao.notification.notification as nfs
import app.dao.trigger.trigger as tr
import app.dao.notification_queue.notification_queue as nq
import app.dao.misc.misc as md

#import app.helpers.misc as misc
from app.helpers.misc import restricted
import app.helpers.misc as misc

import binascii
import os


MAX_PG = 5
MAX_PG_ENTRIES_USERS = 10
MAX_PG_ENTRIES_DATA = 10
MAX_PG_ENTRIES_GRAPH_HOURS = 24

@app.route('/administration', methods=['GET', 'POST'])
@restricted(access_level='admin')
def administration():
    if request.method == 'GET':
        user_cnt = ud.get_count()[1][0]
        apps_cnt = ad.get_count()[1][0]
        devs_cnt = dd.get_count_all()[1][0]
        info = [user_cnt, apps_cnt, devs_cnt]

        return render_template('new/admin/administration.html', info=info)
    elif request.method == 'POST':
        if request.form.getlist('signup') and request.form.getlist('signup')[0] == 'on':
            app.config['USERS_SIGNUP'] = True
        else:
            app.config['USERS_SIGNUP'] = False
        
        return redirect(request.url)


@app.route('/administration/users')
@restricted(access_level='admin')
def administration_users():
    user_cnt = ud.get_count()[1][0]
    apps_cnt = ad.get_count()[1][0]
    devs_cnt = dd.get_count_all()[1][0]
    info = [user_cnt, apps_cnt, devs_cnt]
    
    cur_pg = 1
    users = ud.get_range([MAX_PG_ENTRIES_USERS, (cur_pg-1)*MAX_PG_ENTRIES_USERS])[1]

    return render_template('new/admin/users.html', users=users, info=info)


@app.route('/administration/users/<name>')
@restricted(access_level='admin')
def administration_users_user(name):
    created_apps = ad.get_count_by_user(name)[1][0]
    active_devices = dd.get_count_by_user(name)
    total_activity = md.get_user_data_count(name)[1][0]
    last_activity = md.get_user_data_count_per_day(name)[1][0]
    info = [created_apps, active_devices, total_activity, last_activity]

    return render_template('new/admin/user-dashboard.html', info=info, user=name)


@app.route('/administration/users/<name>/applications')
@restricted(access_level='admin')
def administration_users_user_applications(name):
    apps = ad.get_list(name)[1]
    return render_template('new/admin/user-applications.html', apps=apps, user=name)


@app.route('/administration/users/<name>/new-application', methods=['GET', 'POST'])
@restricted(access_level='admin')
def administration_users_user_application_create(name):
    if request.method == 'GET':
        return render_template('new/admin/user-new-application.html', user=name)
    elif request.method == 'POST':
        if request.form['appname'] == '':
            flash('Application name cannot be empty.', 'danger')
            return render_template(request.url)
        elif request.method == 'POST':
            appkey = misc.rand_str(app.config['APPKEY_LENGTH']).decode('utf-8')
            secure_key = misc.gen_skey_b64(16)
            secure = False

            if request.form.getlist('secure') and request.form.getlist('secure')[0] == 'on':
                secure = True

            res = ad.create(request.form['appname'], appkey, name, request.form['appdesc'], secure, secure_key)
        
            if not res[0]:
                flash('Error: {}'.format(res[1]), 'danger')
                return render_template(request.url)
        
            res = dd.create_table(appkey)
        
            if not res[0]:
                ad.delete(appkey)
                flash('Error: {}'.format(res[1]), 'danger')
                return render_template(request.url)
        
            return redirect(url_for('administration_users_user_applications', name=name))


@app.route('/administration/users/<name>/application/<appkey>')
@restricted(access_level='admin')
def administration_users_user_application(name, appkey):
    ap = list(ad.get(appkey)[1])
    ap[5] = misc.skey_b64_to_hex(ap[5])
    devs = dd.get_list(ap[1])[1]

    return render_template('new/admin/user-application.html', app=ap, devs=devs, user=name)


@app.route('/administration/users/<name>/application/<appkey>/add-device', methods=['GET', 'POST'])
@restricted(access_level='admin')
def administration_users_user_application_add_device(name, appkey):
    if request.method == 'GET':
        ap = ad.get(appkey)
        dev_list = dd.get_list(appkey)
        return render_template('new/admin/user-add-device.html', app=ap[1], free_ids=misc.prep_id_range(dev_list[1]), user=name)
    elif request.method == 'POST':
        res = dd.create(request.form['devname'], request.form['devid'], appkey, request.form['devdesc'])

        if not res[0]:
            flash('Error: {}'.format(res[1]), 'danger')
            return render_template(request.url)
        else:
            res = data.create_table(appkey, request.form['devid'])
        
            if not res[0]:
                dd.delete(appkey, request.form['devid'])
                flash('Error: {}'.format(res[1]), 'danger')
                return render_template(request.url)
            else:
                return redirect(url_for('administration_users_user_application', name=name, appkey=appkey))


@app.route('/administration/users/<name>/application/<appkey>/device/<devid>')
@restricted(access_level='admin')
def administration_users_user_application_device(name, appkey, devid):
    ap = ad.get(appkey)
    dev = dd.get(appkey, devid)

    ld = data.get_last_range(appkey, devid, [MAX_PG_ENTRIES_DATA, 0])
    cnt = data.get_count(appkey, devid)

    ltup = 'Device has not any sent data yet'

    if ld[0] and ld[1][0] != []:
        ltup = ld[1][0][1]

    if ld[0]: 
        return render_template('new/admin/user-device.html', dev=dev[1], app=ap[1], ltup=ltup, data=ld[1], total=cnt[1][0], user=name)
    else:
        return render_template('new/admin/user-device.html', dev=dev[1], app=ap[1], ltup=ltup, data=[], total=cnt[1][0], user=name)


@app.route('/administration/users/<name>/application/<appkey>/alerts')
@restricted(access_level='admin')
def administration_users_user_application_alerts(name, appkey):
    ap = ad.get(appkey)
    alerts = nfs.get_alerts_list(appkey)
    return render_template('new/admin/user-application-alerts.html', alert_list=alerts[1], app=ap[1], user=name)


@app.route('/administration/users/<name>/application/<appkey>/new-alert', methods=['GET', 'POST'])
@restricted(access_level='admin')
def administration_users_user_application_new_alert(name, appkey):
    if request.method == 'GET':
        ap = ad.get(appkey)
        devs = dd.get_list(appkey)
        
        return render_template('new/admin/user-new-alert.html', devs=devs[1], app=ap[1], user=name)
    elif request.method == 'POST':
        # create new notification
        nid = misc.rand_str(app.config['NID_LENGTH']).decode('utf-8')
        dev = dd.get(appkey, request.form['devid'])
        
        try:
            desc = dev[1][0]+'.'+request.form['varname']+' '+request.form['operation']+' '+request.form['avalue']
            res = nfs.create(nid, appkey, request.form['devid'], request.form['alertname'], desc, 'alert', request.form['alertemail'])
            if res[0]:
                # create new function and trigger
                tr.create_function(appkey, request.form['devid'], nid, [request.form['varname'],request.form['operation'],request.form['avalue']])
                tr.create(appkey, request.form['devid'], nid)
                flash('Alert created', 'success')
                return redirect(url_for('administration_users_user_application_alerts', name=name, appkey=appkey))
            else:
                flash('Error creating new alert: {}'.format(res[1]), 'danger')
                return redirect(request.url) 
        except Exception as e:
            flash('Error creating new alert: {}. Make sure you have filled all form fields.'.format(e), 'danger')
            return redirect(request.url) 


@app.route('/administration/users/<name>/application/<appkey>/automation')
@restricted(access_level='admin')
def administration_users_user_application_automation(name, appkey):
    ap = ad.get(appkey)
    ats = nfs.get_automation_list(appkey)
    
    return render_template('new/admin/user-application-automation.html', automations=ats[1], app=ap[1], user=name)


@app.route('/administration/users/<name>/application/<appkey>/new-automation', methods=['GET', 'POST'])
@restricted(access_level='admin')
def administration_users_user_application_new_automation(name, appkey):
    if request.method == 'GET':
        ap = ad.get(appkey)
        devs = dd.get_list(appkey)
        
        return render_template('new/admin/user-application-new-automation.html', devs=devs[1], app=ap[1], user=name)
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
                tr.create_function(appkey, request.form['devid'], nid, [request.form['varname'],request.form['operation'],request.form['avalue']])
                tr.create(appkey, request.form['devid'], nid)
                flash('Automation created', 'success')
                return redirect(url_for('administration_users_user_application_automation', name=name, appkey=appkey))
            else:
                flash('Error creating new alert: {}'.format(res[1]), 'danger')
                return redirect(request.url) 
        except Exception as e:
            flash('Error creating new alert: {}. Make sure you have filled all form fields.'.format(e), 'danger')
            return redirect(request.url) 


@app.route('/administration/users/<name>/application/<appkey>/delete')
@restricted(access_level='admin')
def administration_users_user_application_delete(name, appkey):
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
        return redirect(url_for('administration_users_user_application_settings', name=name, appkey=appkey))
    else:
        flash('Application deleted.', 'success')
        return redirect(url_for('administration_users_user_applications', name=name))


@app.route('/administration/users/<name>/application/<appkey>/settings', methods=['GET', 'POST'])
@restricted(access_level='admin')
def administration_users_user_application_settings(name, appkey):
    if request.method == 'GET':
        ap = ad.get(appkey)

        return render_template('new/admin/user-application-settings.html', app=ap[1], user=name)
    elif request.method == 'POST':
        if request.form.getlist('secure') and request.form.getlist('secure')[0] == 'on':
            secure = True
        else:
            secure = False
        
        res = ad.update(appkey, request.form['appname'], request.form['appdesc'], secure)
    
        if not res[0]:
            flash('Error: {}'.format(res[1]), 'danger')
            return render_template(request.url)
    
        return redirect(request.url)


@app.route('/administration/users/<name>/application/<appkey>/delete-<ntype>')
@restricted(access_level='admin')
def administration_users_user_application_notification_remove(name, appkey, ntype):
    nq.delete(appkey, request.args.get('devid'), request.args.get('id'))
    tr.delete(appkey, request.args.get('devid'), request.args.get('id'))
    tr.delete_function(appkey, request.args.get('devid'), request.args.get('id'))
    res = nfs.delete(appkey, request.args.get('devid'), request.args.get('id'))

    if res[0]:
        flash('{} removed'.format(ntype.capitalize()), 'success')
        return '', 200
    else:
        flash('{} cannot be removed : {}'.format(ntype.capitalize(), res[1]), 'danger')
        return '', 500


@app.route('/administration/users/<name>/application/<appkey>/device/<devid>/variables')
@restricted(access_level='admin')
def administration_users_user_application_device_variables(name, appkey, devid):
        last = data.get_last_n(appkey, devid, 1)
        if last[0]:
            select = '<select class="form-control" id="varname" name="varname" onchange="validate_form();" required>'
            select += '<option value="-">Select Variable</option>'
            for k in last[1][0][2]:
                select += '<option>'+k+'</option>'
            select += '</select>'
            return select


@app.route('/administration/users/<name>/application/<appkey>/device/<devid>/data/<var>/<dest>/<page>')
@restricted(access_level='admin')
def administration_users_user_application_device_data(name, appkey, devid, var, dest, page):
    if dest == 'graph':
        last = data.get_last_hours(appkey, devid, MAX_PG_ENTRIES_GRAPH_HOURS, int(page))
        arr = '[["Time", "{}"],'.format(var)
        if last[0]:
            for d in last[1]:
                arr += '[new Date('+str(d[0])+'*1000),'+str(d[2][var])+'],'
            arr += ']'
        return arr
    elif dest == 'table':
        # for table <cnt> is in items
        last = data.get_last_range(appkey, devid, [MAX_PG_ENTRIES_DATA, (int(page)-1)*MAX_PG_ENTRIES_DATA])
        t = ''
        if last[0]:
            for d in last[1]:
                t += '<tr><th>'+d[1]+'</th><th>'+str(d[2][var])+'</th></tr>'
        return t


@app.route('/administration/users/<name>/application/<appkey>/device/<devid>/configure', methods=['GET', 'POST'])
@restricted(access_level='admin')
def administration_users_user_application_device_configuration(name, appkey, devid):
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
        
        return render_template('new/admin/user-application-device-configuration.html', dev=dev, app=ap, config_list=config_list, user=name)
    elif request.method == 'POST':
        base64_args = misc.pend_base64_encode(request.form['arg'], request.form['confid'])
        pend.create(appkey, devid, base64_args)
        
        flash('Message enqueued', 'success')
        return '', 201


@app.route('/administration/users/<name>/application/<appkey>/device/<devid>/remove-configuration')
@restricted(access_level='admin')
def administration_users_user_application_device_configuration_remove(name, appkey, devid):
    res = pend.delete(appkey, devid, request.args.get('conf')+'_')

    if res[0]:
        flash('Configuration message successfully removed.','success')
    else:
        flash('Error removing configuration message: {}'.format(res[1]), 'danger')
    
    return '', 200


@app.route('/administration/users/<name>/application/<appkey>/device/<devid>/download-csv')
@restricted(access_level='admin')
def administration_users_user_application_device_download_csv(name, appkey, devid):
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


@app.route('/administration/users/<name>/chart-update')
@restricted(access_level='admin')
def administration_users_user_chart_update(name):
    day_chart_values = md.get_user_data_count_per_hour_period(name, 11)[1]
    day_chart_values = [x[0] for x in day_chart_values]
    day_chart_labels = [misc.local_hour(x) for x in range(11,-1,-1)]
    day_chart = [day_chart_labels, day_chart_values]

    week_chart_values = md.get_user_data_count_per_day_period(name, 6)[1]
    week_chart_values = [x[0] for x in week_chart_values]
    week_chart_labels = [misc.local_weekday(x) for x in range(6,-1,-1)]
    week_chart = [week_chart_labels, week_chart_values]
    
    return "[{}, {}]".format(day_chart, week_chart)


@app.route('/administration/users/<name>/recent-activity')
@restricted(access_level='admin')
def administration_users_user_recent_activity(name):
    if 'name' in session:
        recent_activity = md.get_recent_activity(name)[1]
        ra = ''
        
        for r in recent_activity:
            ra += '<tr><th scope="row">'+r[1]+'</th><th>'+r[2]+'</th><th>'+r[0]+'</th><th>'+str(r[3])+'</th></tr>'

        return ra, 200
    else:
        return '', 401


@app.route('/administration/users/table/<page>')
@restricted(access_level='admin')
def administration_users_table(page):
    users = ud.get_range_name(request.args.get('name'), [MAX_PG_ENTRIES_USERS, (int(page)-1)*MAX_PG_ENTRIES_USERS])[1]
    users = [[u[0],u[2]] for u in users]

    return str(users), 200


@app.route('/administration/users/new-user', methods=['POST', 'GET'])
@restricted(access_level='admin')
def administration_users_new_user():
    if request.method == 'GET':
        return render_template('new/admin/new-user.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        role = request.form['role']
        
        if (username == '' or password == ''):
            flash('Username or password fields cannot be empty', 'danger')
            return redirect(request.url)
        elif (len(password) < 8):
            flash('Password length must be at least 8 characters.', 'danger')
            return redirect(request.url)
        else:
            res = ud.create(username, password, role)
            if (not res[0]):
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url)
            else:
                return redirect(url_for('administration/users', name=username))

