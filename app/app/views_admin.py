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
    cur_pg = 1
    users = ud.get_range([MAX_PG_ENTRIES_USERS, (cur_pg-1)*MAX_PG_ENTRIES_USERS])[1]

    return render_template('new/admin/users.html', users=users)


@app.route('/administration/users/<name>')
@restricted(access_level='admin')
def administration_users_user(name):
    cur_pg = 1
    users = ud.get_range([MAX_PG_ENTRIES_USERS, (cur_pg-1)*MAX_PG_ENTRIES_USERS])[1]

    return render_template('new/admin/user.html', users=users)


@app.route('/administration/users/table-<option>/<page>')
@restricted(access_level='admin')
def administration_users_table(option, page):
    if option == 'filter':
        users = ud.get_range_name(request.args.get('name'), [MAX_PG_ENTRIES_USERS, (int(page)-1)*MAX_PG_ENTRIES_USERS])[1]
    elif option == 'page':
        users = ud.get_range([MAX_PG_ENTRIES_USERS, (int(page)-1)*MAX_PG_ENTRIES_USERS])[1]

    users = [[u[0],u[2]] for u in users]

    return str(users), 200

