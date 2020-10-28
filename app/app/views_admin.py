from app import app

from flask import render_template, request, redirect, url_for, session, flash, after_this_request, send_from_directory

import app.dao.user.user as ud
import app.dao.application.application as ad
import app.dao.device.device as dd
import app.dao.gateway.gateway as gd
import app.dao.pend.pend as pend
import app.dao.data.data as data
import app.dao.notification.notification as nfs
import app.dao.trigger.trigger as tr
import app.dao.misc.misc as md

#import app.helpers.misc as misc
from app.helpers.decorators import restricted
import app.helpers.device_data_model as ddm
import app.helpers.misc as misc
import app.helpers.gateway_management as gwm

import binascii
import os


MAX_PG = 5
MAX_PG_ENTRIES_USERS = 10
MAX_PG_ENTRIES_DATA = 10
MAX_PG_ENTRIES_GRAPH_HOURS = 24


@app.route('/administration', methods=['GET', 'POST'])
@restricted('admin')
def administration():
    if request.method == 'GET':
        user_cnt = ud.get_count()[1][0]
        apps_cnt = ad.get_count()[1][0]
        devs_cnt = dd.get_count_all()[1][0]
        info = [user_cnt, apps_cnt, devs_cnt]

        return render_template('views/admin/administration.html', info=info, administration="active")
    elif request.method == 'POST':
        if request.form.getlist('signup') and request.form.getlist('signup')[0] == 'on':
            app.config['USERS_SIGNUP'] = True
        else:
            app.config['USERS_SIGNUP'] = False
        
        app.logger.warning('Users signup changed to %s by %s', app.config['USERS_SIGNUP'], session['name'])

        return redirect(request.url)


@app.route('/administration/users')
@restricted('admin')
def administration_users():
    user_cnt = ud.get_count()[1][0]
    apps_cnt = ad.get_count()[1][0]
    devs_cnt = dd.get_count_all()[1][0]
    info = [user_cnt, apps_cnt, devs_cnt]
    
    cur_pg = 1
    users = ud.get_range([MAX_PG_ENTRIES_USERS, (cur_pg-1)*MAX_PG_ENTRIES_USERS])[1]

    return render_template('views/admin/users.html', users=users, info=info, users_link="active")


@app.route('/administration/<name>')
@restricted('admin', True)
def administration_user(name):
    created_apps = ad.get_count_by_user(name)[1][0]
    active_devices = dd.get_count_by_user(name)
    total_activity = md.get_user_data_count(name)[1][0]
    last_activity = md.get_user_data_count_per_day(name)[1][0]
    info = [created_apps, active_devices, total_activity, last_activity]

    return render_template('views/admin/user-dashboard.html', info=info, user=name, administration="active")

@app.route('/administration/<name>/applications')
@restricted('admin', True)
def administration_user_applications(name):
    apps = ad.get_list(name)[1]
    return render_template('views/admin/user-applications.html', apps=apps, user=name, administration="active")


@app.route('/administration/<name>/new-application', methods=['GET', 'POST'])
@restricted('admin', True)
def administration_user_new_application(name):
    if request.method == 'GET':
        return render_template('views/admin/user-new-application.html', user=name, administration="active")
    elif request.method == 'POST':
        if request.form['appname'] == '':
            flash('Application name cannot be empty.', 'danger')
            return redirect(request.url)
        else:
            appkey = misc.rand_str(app.config['APPKEY_LENGTH']).decode('utf-8')
            secure_key = misc.gen_skey_b64(16)
            secure = False

            if request.form.getlist('secure') and request.form.getlist('secure')[0] == 'on':
                secure = True

            res = ad.create(request.form['appname'], appkey, name, request.form['appdesc'], secure, secure_key)
        
            if not res[0]:
                app.logger.error('Administrator %s failed to create new application for %s - %s', session['name'], name, res[1])
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url)
        
            res = dd.create_table(appkey)
        
            if not res[0]:
                ad.delete(appkey)
                app.logger.error('Administrator %s failed to create new application for %s - %s', session['name'], name, res[1])
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url)
            else:
                app.logger.warning('Administrator %s created new application %s for %s', session['name'], appkey, name)

            return redirect(url_for('administration_user_applications', name=name))


@app.route('/administration/<name>/application/<appkey>')
@restricted('admin', True)
def administration_user_application(name, appkey):
    ap = list(ad.get(appkey)[1])
    ap[5] = misc.skey_b64_to_hex(ap[5])
    devs = dd.get_list(ap[1])[1]

    return render_template('views/admin/user-application.html', app=ap, devs=devs, user=name, administration="active")


@app.route('/administration/<name>/application/<appkey>/add-device', methods=['GET', 'POST'])
@restricted('admin', True)
def administration_user_application_add_device(name, appkey):
    if request.method == 'GET':
        ap = ad.get(appkey)
        dev_list = dd.get_list(appkey)
        return render_template('views/admin/user-application-add-device.html', app=ap[1], free_ids=misc.prep_id_range(dev_list[1]), models=ddm.MODELS, user=name, administration="active")
    elif request.method == 'POST':
        if dd.check_devid(appkey, request.form['devid']):
            ddmin = ddm.extract(request)
            res = dd.create(request.form['devname'], request.form['devid'], appkey, request.form['devdesc'], ddmin)

            if not res[0]:
                app.logger.error('Administrator %s failed to add device application %s for %s - %s', session['name'], appkey, name, res[1])
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url)
            
            res = data.create_table(appkey, request.form['devid'])
        
            if not res[0]:
                dd.delete(appkey, request.form['devid'])
                app.logger.error('Administrator %s failed to add device application %s for %s - %s', session['name'], appkey, name, res[1])
                flash('Error: {}'.format(res[1]), 'danger')
                return rendirect(request.url)
            
            app.logger.warning('Administrator %s added new device %s application %s for %s', session['name'], request.form['devid'], appkey, name)
            
            return redirect(url_for('administration_user_application', name=name, appkey=appkey))
        else:
            app.logger.info('%s %s failed to add new device %s for application %s. Cause: existing devid', session['role'], session['name'], request.form['devname'], appkey)
            flash('Error: Selected Device ID already used, pick another one.', 'danger')
            return redirect(request.url)


@app.route('/administration/<name>/application/<appkey>/device/<devid>')
@restricted('admin', True)
def administration_user_application_device(name, appkey, devid):
    ap = ad.get(appkey)
    dev = dd.get(appkey, devid)

    ld = data.get_last_n(appkey, devid, 1)
    cnt = data.get_count(appkey, devid)

    ltup = 'Device has not any sent data yet'

    if ld[0] and ld[1][0] != []:
        ltup = ld[1][0][1]

    return render_template('views/admin/user-application-device.html', dev=dev[1], app=ap[1], ltup=ltup, total=cnt[1][0], user=name, table_max=MAX_PG_ENTRIES_DATA, administration="active")


@app.route('/administration/<name>/application/<appkey>/device/<devid>/settings', methods=['GET', 'POST'])
@restricted('admin', True)
def administration_user_application_device_settings(name, appkey, devid):
    if request.method == 'GET':
        ap = ad.get(appkey)
        dev = dd.get(appkey, devid)

        return render_template('views/admin/user-application-device-settings.html', app=ap[1], dev=dev[1], models=ddm.MODELS, user=name, administration="active")
    elif request.method == 'POST':
        ddmin = ddm.extract(request)
        res = dd.update(appkey, devid, request.form['devname'], request.form['devdesc'], ddmin)
    
        if not res[0]:
            app.logger.error('Administrator %s failed to change settings for device %s application %s for %s - %s', session['name'], devid, appkey, name, res[1])
            flash('Error: {}'.format(res[1]), 'danger')
            return redirect(request.url)
    
        app.logger.warning('Administrator %s changed settings for device %s application %s for %s', session['name'], devid, appkey, name)
       
        flash('Settings saved', 'success')
        return redirect(request.url)


@app.route('/administration/<name>/application/<appkey>/device/<devid>/delete')
@restricted('admin', True)
def administration_user_application_device_delete(name, appkey, devid):
    nfss = nfs.get_per_device(appkey, devid)
    for nf in nfss[1]:
        tr.delete(appkey, devid, nf[0])
        tr.delete_function(appkey, devid, nf[0])
        nfs.delete(appkey, devid, nf[0])

    data.delete_table(appkey, devid)
    res = dd.delete(appkey, devid)

    app.logger.warning('Administrator %s deleted device %s application %s for %s', session['name'], devid, appkey, name)

    return redirect(url_for('administration_user_application', name=name, appkey=appkey))


@app.route('/administration/<name>/application/<appkey>/alerts')
@restricted('admin', True)
def administration_user_application_alerts(name, appkey):
    ap = ad.get(appkey)
    alerts = nfs.get_alerts_list(appkey)
    return render_template('views/admin/user-application-alerts.html', alert_list=alerts[1], app=ap[1], user=name, administration="active")


@app.route('/administration/<name>/application/<appkey>/new-alert', methods=['GET', 'POST'])
@restricted('admin', True)
def administration_user_application_new_alert(name, appkey):
        if request.method == 'GET':
            ap = ad.get(appkey)
            devs = dd.get_list(appkey)
            
            return render_template('views/admin/user-application-new-alert.html', devs=devs[1], app=ap[1], user=name, administration="active")
        elif request.method == 'POST':
            # create new notification
            nid = misc.rand_str(app.config['NID_LENGTH']).decode('utf-8')
            dev = dd.get(appkey, request.form['devid'])
            
            try:
                desc = dev[1][0]+'.'+request.form['varname']+' '+request.form['operation']+' '+request.form['avalue']
                res = nfs.create(nid, appkey, request.form['devid'], request.form['alertname'], desc, 'alert_'+request.form['alerttype'], request.form['alertemail'])
                if res[0]:
                    # create new function and trigger
                    tr.create_function_rt(appkey, request.form['devid'], nid, [request.form['varname'],request.form['operation'],request.form['avalue']],'alert_'+request.form['alerttype'], request.form['alertemail'])
                    tr.create(appkey, request.form['devid'], nid)
                    app.logger.warning('Administrator %s created alert %s for application %s for %s', session['name'], nid, appkey, name)
                    flash('Alert created', 'success')
                    return redirect(url_for('administration_user_application_alerts', name=name, appkey=appkey))
                else:
                    app.logger.error('Administrator %s failed to create alert for application %s for %s - %s', session['name'], appkey, name, res[1])
                    flash('Error creating new alert: {}'.format(res[1]), 'danger')
                    return redirect(request.url) 
            except Exception as e:
                app.logger.error('Administrator %s failed to create alert for application %s for %s - %s', session['name'], appkey, name, e)
                flash('Error creating new alert: {}. Make sure you have filled all form fields.'.format(e), 'danger')
                return redirect(request.url) 


@app.route('/administration/<name>/application/<appkey>/automation')
@restricted('admin', True)
def administration_user_application_automation(name, appkey):
    ap = ad.get(appkey)
    ats = nfs.get_automation_list(appkey)
    
    return render_template('views/admin/user-application-automation.html', automations=ats[1], app=ap[1], user=name, administration="active")


@app.route('/administration/<name>/application/<appkey>/new-automation', methods=['GET', 'POST'])
@restricted('admin', True)
def administration_user_application_new_automation(name, appkey):
    if request.method == 'GET':
        ap = ad.get(appkey)
        devs = dd.get_list(appkey)
        
        return render_template('views/admin/user-application-new-automation.html', devs=devs[1], app=ap[1], user=name, administration="active")
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
                app.logger.warning('Administrator %s created automation %s for application %s for %s', session['name'], nid, appkey, name)
                flash('Automation created', 'success')
                return redirect(url_for('administration_user_application_automation', name=name, appkey=appkey))
            else:
                app.logger.error('Administrator %s failed to create automation for application %s for %s - %s', session['name'], appkey, name, res[1])
                flash('Error creating new alert: {}'.format(res[1]), 'danger')
                return redirect(request.url) 
        except Exception as e:
            app.logger.error('Administrator %s failed to create automation for application %s for %s - %s', session['name'], appkey, name, e)
            flash('Error creating new alert: {}. Make sure you have filled all form fields.'.format(e), 'danger')
            return redirect(request.url) 


@app.route('/administration/<name>/application/<appkey>/delete')
@restricted('admin', True)
def administration_user_application_delete(name, appkey):
    devs = dd.get_list(appkey)

    for dev in devs[1]:
        data.delete_table(appkey, dev[1])
        # delete notifications
        nfss = nfs.get_per_device(appkey, dev[1])
        for nf in nfss[1]:
            tr.delete(appkey, dev[1], nf[0])
            tr.delete_function(appkey, dev[1], nf[0])
            nfs.delete(appkey, dev[1], nf[0])

    dd.delete_table(appkey)

    res = ad.delete(appkey)

    if not res[0]:
        app.logger.error('Administrator %s failed to delete application %s for %s - %s', session['name'], appkey, name, res[1])
        flash('Error deleting application: {}'.format(res[1]), 'danger')
        return redirect(url_for('administration_user_application_settings', name=name, appkey=appkey))
    else:
        app.logger.warning('Administrator %s deleted application %s for %s', session['name'], appkey, name)
        flash('Application deleted.', 'success')
        return redirect(url_for('administration_user_applications', name=name))


@app.route('/administration/<name>/application/<appkey>/settings', methods=['GET', 'POST'])
@restricted('admin', True)
def administration_user_application_settings(name, appkey):
    if request.method == 'GET':
        ap = ad.get(appkey)

        return render_template('views/admin/user-application-settings.html', app=ap[1], user=name, administration="active")
    elif request.method == 'POST':
        if request.form.getlist('secure') and request.form.getlist('secure')[0] == 'on':
            secure = True
        else:
            secure = False
        
        res = ad.update(appkey, request.form['appname'], request.form['appdesc'], secure)
    
        if not res[0]:
            app.logger.error('Administrator %s failed to change settings for application %s for %s - %s', session['name'], appkey, name, res[1])
            flash('Error: {}'.format(res[1]), 'danger')
            return redirect(request.url)
   
        app.logger.warning('Administrator %s changed settings for application %s for %s', session['name'], appkey, name)
        
        flash('Settings saved', 'success')
        return redirect(request.url)


@app.route('/administration/<name>/application/<appkey>/delete-<ntype>')
@restricted('admin', True)
def administration_user_application_notification_remove(name, appkey, ntype):
    tr.delete(appkey, request.args.get('devid'), request.args.get('id'))
    tr.delete_function(appkey, request.args.get('devid'), request.args.get('id'))
    res = nfs.delete(appkey, request.args.get('devid'), request.args.get('id'))

    if res[0]:
        app.logger.warning('Administrator %s deleted %s %s for application %s for %s', session['name'], ntype, request.args.get('id'), appkey, name)
        flash('{} removed'.format(ntype.capitalize()), 'success')
        return '', 200
    else:
        app.logger.error('Administrator %s failed to delete %s %s for application %s for %s - %s', session['name'], ntype, request.args.get('id'), appkey, name, res[1])
        flash('{} cannot be removed : {}'.format(ntype.capitalize(), res[1]), 'danger')
        return '', 500


@app.route('/administration/<name>/application/<appkey>/device/<devid>/variables')
@restricted('admin', True)
def administration_user_application_device_variables(name, appkey, devid):
    dev = dd.get(appkey, devid)[1]
    select = '<select class="form-control" id="varname" name="varname" onchange="validate_form();" required>'
    select += '<option value="-">Select Variable</option>'
    for k in dev[3]['format']:
        select += '<option>'+k+'</option>'
    select += '</select>'
    return select


@app.route('/administration/<name>/application/<appkey>/device/<devid>/data/<var>/<dest>/<page>')
@restricted('admin', True)
def administration_user_application_device_data(name, appkey, devid, var, dest, page):
    dev = dd.get(appkey, devid)[1]
    if dest == 'graph':
        last = data.get_last_hours(appkey, devid, MAX_PG_ENTRIES_GRAPH_HOURS, int(page))
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

@app.route('/administration/<name>/application/<appkey>/device/<devid>/geo')
@restricted('admin')
def administration_user_application_device_geo(name, appkey, devid):
    dev = dd.get(appkey, devid)[1]
    if 'lat' in dev[3]['format'] and 'lon' in dev[3]['format']:
        ld = data.get_last_n(appkey, devid, 1)[1]
        d = ddm.read_data(ld[0][2].tobytes(), dev[3])
        return str([d['lat'],d['lon']]), 200
    return '', 404


@app.route('/administration/<name>/application/<appkey>/device/<devid>/configure', methods=['GET', 'POST'])
@restricted('admin', True)
def administration_user_application_device_configuration(name, appkey, devid):
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
        
        return render_template('views/admin/user-application-device-configuration.html', dev=dev, app=ap, config_list=config_list, user=name, administration="active")
    elif request.method == 'POST':
        base64_args = misc.pend_base64_encode(request.form['arg'], request.form['confid'])
        pend.create(appkey, devid, base64_args)
       
        app.logger.warning('Administrator %s sent config message %s for device %s application %s for %s', session['name'], base64_args, devid, appkey, name)

        flash('Message enqueued', 'success')
        return '', 201


@app.route('/administration/<name>/application/<appkey>/device/<devid>/remove-configuration')
@restricted('admin', True)
def administration_user_application_device_configuration_remove(name, appkey, devid):
    res = pend.delete(appkey, devid, request.args.get('conf')+'_')

    if res[0]:
        app.logger.warning('Administrator %s deleted config message %s for device %s application %s for %s', session['name'], request.args.get('conf'), devid, appkey, name)
        flash('Configuration message removed.','success')
    else:
        app.logger.error('Administrator %s failed to delete config message %s for device %s application for %s - %s', session['name'], request.args.get('conf'), devid, appkey, name, res[1])
        flash('Error removing configuration message: {}'.format(res[1]), 'danger')
    
    return '', 200


@app.route('/administration/<name>/application/<appkey>/device/<devid>/download-csv')
@restricted('admin', True)
def administration_user_application_device_download_csv(name, appkey, devid):
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
            decoded = ddm.read_data(row[2].tobytes(), dev[3])
            for k, v in decoded.items():
                f.write(str(v))
                f.write(',')
            f.write('\n')
    
    app.logger.warning('Administrator %s downloaded csv data for device %s application %s for %s', session['name'], devid, appkey, name)

    return send_from_directory(app.config['DATA_DOWNLOAD_DIR'], fn, as_attachment=True)


@app.route('/administration/<name>/chart-update')
@restricted('admin', True)
def administration_user_chart_update(name):
    day_chart_values = md.get_user_data_count_per_hour_period(name, 11)[1]
    day_chart_values = [x[0] for x in day_chart_values]
    day_chart_labels = [misc.local_hour(x) for x in range(11,-1,-1)]
    day_chart = [day_chart_labels, day_chart_values]

    week_chart_values = md.get_user_data_count_per_day_period(name, 6)[1]
    week_chart_values = [x[0] for x in week_chart_values]
    week_chart_labels = [misc.local_weekday(x) for x in range(6,-1,-1)]
    week_chart = [week_chart_labels, week_chart_values]
    
    return "[{}, {}]".format(day_chart, week_chart)


@app.route('/administration/<name>/recent-activity')
@restricted('admin', True)
def administration_user_recent_activity(name):
    recent_activity = md.get_recent_activity(name)[1]
    ra = ''
    
    for r in recent_activity:
        dev = dd.get(r[5], r[6])[1]
        hrefapp = '<th scope="row"><a href="application/{}">{}</a></th>'.format(r[5], r[1])
        hrefdev = '<th><a href="application/{}/device/{}">{}</a></th>'.format(r[5], r[6], r[2])
        ra += '<tr>'+hrefapp+hrefdev+'<th>'+r[0]+'</th><th>'+str(ddm.read_data(r[3].tobytes(), dev[3]))+'</th></tr>'

    return ra, 200


@app.route('/administration/users/table/<page>')
@restricted('admin')
def administration_users_table(page):
    users = ud.get_range_name(request.args.get('name'), [MAX_PG_ENTRIES_USERS, (int(page)-1)*MAX_PG_ENTRIES_USERS])[1]
    users = [[u[0],u[2]] for u in users]

    return str(users), 200


@app.route('/administration/new-user', methods=['POST', 'GET'])
@restricted('admin')
def administration_new_user():
    if request.method == 'GET':
        return render_template('views/admin/new-user.html', administration="active")
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
            if not res[0]:
                app.logger.error('Administrator %s failed to create new user %s - %s', session['name'], username, res[1])
                flash('Error: {}'.format(res[1]), 'danger')
                return redirect(request.url)
            else:
                app.logger.warning('Administrator %s created new user %s', session['name'], username)
                flash('User {} created.'.format(username), 'success')
                return redirect(url_for('administration_user', name=username))


@app.route('/administration/<name>/settings', methods=['GET', 'POST'])
@restricted('admin', True)
def administration_user_settings(name):
    user = ud.get(name)
    if user[0] and misc.grant_view(user[1][2], session['role']):
        if request.method == 'GET':
            return render_template('views/admin/user-settings.html', user=name, user_role=user[1][2], administration="active")
        else:
            if request.form['name'] != name:
                res = ud.update_name(name, request.form['name'])
                if not res[0]:
                    flash('Error: {}'.format(res[1]), 'danger')
                    return redirect(request.url);
            if request.form['password'] != '':
                res = ud.update_password(name, request.form['password'].encode('utf-8'))
                if not res[0]:
                    flash('Error: {}'.format(res[1]), 'danger')
                    app.logger.error('Administrator %s failed to update password for user %s - %s', session['name'], name, res[1])
                    return redirect(request.url)
            if request.form['role'] != user[1][2]:
                res = ud.update_role(name, request.form['role'])
                if not res[0]:
                    app.logger.error('Administrator %s failed to update role for user %s - %s', session['name'], name, res[1])
                    flash('Error: {}'.format(res[1]), 'danger')
                    return redirect(request.url)
                
            app.logger.warning('Administrator %s changed settings for user %s', session['name'], name)
            flash('Settings saved.', 'success')
            return redirect(request.url)
    else:
        flash('Access denied' ,'danger')
        return redirect(url_for('administration_user', name=name))


@app.route('/administration/<name>/delete-account')
@restricted('admin', True)
def administration_user_delete_account(name):
    user = ud.get(name)
    if user[0] and misc.grant_view(user[1][2], session['role']):
        app_list = ad.get_list(user[1][0])

        res = (True,)
        if app_list[0]:
            for a in app_list[1]:
                devs = dd.get_list(a[1])
                for dev in devs[1]:
                    res = data.delete_table(a[1], dev[1])
                    if not res[0]:
                        break
    
                if res[0]:
                    res = dd.delete_table(a[1])
                    
                if res[0]:
                    res = ad.delete(a[1])

                if not res[0]:
                    break

        if res[0]:
            res = ud.delete(user[1][0])

        if not res[0]:
            flash('Error: {}'.format(res[1]), 'danger')
            app.logger.error('Administrator %s failed to delete user %s - %s', session['name'], name, res[1])
            return render_template('views/admin/user-settings.html', user=name, administration="active")
        else:
            app.logger.warning('Administrator %s deleted user %s', session['name'], name)
            flash('User {} was deleted'.format(name), 'success')
            return redirect(url_for('administration_users'))
    else:
        app.logger.critical('Administrator %s with role attempted to delete user %s with role %s', session['name'], session['role'], name, user[1][2])
        flash('Warning: the user is admin or does not exist.' ,'danger')
        return redirect(url_for('administration_user_settings', name=name))


@app.route('/administration/gateways', methods=["GET", "DELETE"])
@restricted('admin')
def administration_gateways():
    user_cnt = ud.get_count()[1][0]
    apps_cnt = ad.get_count()[1][0]
    devs_cnt = dd.get_count_all()[1][0]
    info = [user_cnt, apps_cnt, devs_cnt]
    
    gws = gd.get_all()[1]

    return render_template('views/admin/gateways.html', utcnow=misc.get_utc(), info=info, gws=gws)


@app.route('/administration/gateway/<gwid>', methods=["GET", "POST", "DELETE"])
@restricted('admin')
def administration_gateway(gwid):
    user_cnt = ud.get_count()[1][0]
    apps_cnt = ad.get_count()[1][0]
    devs_cnt = dd.get_count_all()[1][0]
    info = [user_cnt, apps_cnt, devs_cnt]
    
    gw = gd.get(gwid)[1]
    gw['secure_key'] = misc.skey_b64_to_hex(gw['secure_key']).decode('UTF-8')

    return render_template('views/admin/gateway.html', utcnow=misc.get_utc(), info=info, gw=gw, protocols=gwm.PROTOCOLS)


@app.route('/administration/new-gateway', methods=['GET', 'POST'])
@restricted('admin')
def administration_new_gateway():
    if request.method == 'GET':
        return render_template('views/admin/new-gateway.html', administration="active", protocols=gwm.PROTOCOLS)
    elif request.method == 'POST':
        secure_key = misc.gen_skey_b64(16)

        res = gd.create(request.form['gwname'], request.form['gwid'], request.form['gwprotocol'], request.form['gwdesc'], secure_key, request.form['gwtelemetry'])
        if not res[0]:
            app.logger.error('Administrator %s failed to create new gateway - %s', res[1])
            flash('Error: {}'.format(res[1]), 'danger')
            return redirect(request.url)
    
        return redirect(url_for('administration_gateways'))


@app.route('/administration/gateway/<gwid>/settings', methods=["GET", "POST"])
@restricted('admin')
def administration_gateway_settings(gwid):
    if request.method == "GET":
        gw = gd.get(gwid)[1]
        gw['secure_key'] = misc.skey_b64_to_hex(gw['secure_key']).decode('UTF-8')

        return render_template('views/admin/gateway-settings.html', utcnow=misc.get_utc(), gw=gw, protocols=gwm.PROTOCOLS)
    elif request.method == "POST":
        res = gd.update(request.form['gwname'], request.form['gwid'], request.form['gwprotocol'], request.form['gwdesc'], request.form['gwtelemetry'])
        if not res[0]:
            app.logger.error('Administrator %s failed to update new gateway - %s', session['name'], res[1])
            flash('Error: {}'.format(res[1]), 'danger')
            return redirect(request.url)
    
        return redirect(url_for('administration_gateway', gwid=gwid))

@app.route('/administration/gateway/<gwid>/delete', methods=["DELETE"])
@restricted('admin')
def administration_gateway_delete(gwid):
    res = gd.delete(gwid)
    if res[0]:
        flash("Gateway '{}' deleted.".format(gwid), 'success')
        return redirect(url_for('administration_gateways'))
    else:
        flash('Error: {}'.format(res[1]), 'danger')
        return redirect(url_for('administration_gateway', gwid=gwid))
