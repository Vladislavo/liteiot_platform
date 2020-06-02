from app import app

from flask import render_template, request, redirect, url_for, session, flash

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

#import binascii


MAX_PG = 5
MAX_PG_ENTRIES_USERS = 10

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

