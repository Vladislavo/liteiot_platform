from app import app
from flask import session,flash,redirect,url_for
from functools import wraps

import app.dao.user.user as ud
import app.dao.application.application as ad

from app.helpers.misc import grant_view

def restricted(access_level, user_protect=False):
    def user_control(f):
        @wraps(f)
        def restricted_function(*args, **kwargs):
            if 'role' in session:
                if not grant_view(access_level, session['role']):
                    flash('Access denied.', 'danger')
                    return redirect(url_for('index'))
                if user_protect:
                    user = ud.get(kwargs['name'])
                    if not user[0] or not grant_view(user[1][2], session['role']):
                        flash('Access denied.', 'danger')
                        return redirect(url_for('index'))
                return f(*args, **kwargs)
            return redirect(url_for('login'))
        return restricted_function
    return user_control

def application_protected(f):
    @wraps(f)
    def protected_function(*args, **kwargs):
        ap = ad.get(kwargs['appkey'])
        if not ap[0] or ap[1][2] != session['name']:
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return protected_function
