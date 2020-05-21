from psycopg2 import sql
from app.helpers.misc import with_psql, utc_roundhour, utc_roundday
import app.dao.application.application as ad
import app.dao.device.device as dd

# appkeys is a list of tuples [(app1), (app2), ..., (appn)]
# devids is a list of lists of tuples [[(dev1),...],[(dev1),...]]
@with_psql
def get_user_data_count(cur, username):
    apps = ad.get_list(username)[1]
    devs = []
    
    for a in apps:
        devs.append(dd.get_list(a[1])[1])

    query = 'WITH t AS ('
    i = 0
    for a in apps:
        for d in devs[i]:
           query += 'SELECT COUNT(*) FROM dev_{}_{} UNION ALL '.format(a[1], d[1])
        i += 1
    query = query[0:-9]
    query += ') SELECT SUM(count) FROM t'

    cur.execute(query, ())
    
    return (True,cur.fetchone())


@with_psql
def get_user_data_count_per_hour(cur, username, hour):
    apps = ad.get_list(username)[1]
    devs = []
    
    for a in apps:
        devs.append(dd.get_list(a[1])[1])

    utc_hour = utc_roundhour(hour)

    query = 'WITH t AS ('
    i = 0
    for a in apps:
        for d in devs[i]:
           query += 'SELECT COUNT(*) FROM dev_{}_{} UNION ALL '.format(a[1], d[1])
        i += 1
    query = query[0:-10]
    query += ') SELECT SUM(count) FROM t WHERE utc > {} AND utc < {}'.format(utc_hour, utc_hour+60*60)

    #print(query)
    cur.execute(query, ())
    
    return (True,cur.fetchone())


@with_psql
def get_user_data_count_per_day(cur, username, day=0):
    apps = ad.get_list(username)[1]
    devs = []
    
    for a in apps:
        devs.append(dd.get_list(a[1])[1])

    utc_day = utc_roundday(day)

    query = 'WITH t AS ('
    i = 0
    for a in apps:
        for d in devs[i]:
           query += 'SELECT utc FROM dev_{}_{} UNION ALL '.format(a[1], d[1])
        i += 1
    query = query[0:-10]
    query += ') SELECT COUNT(*) FROM t WHERE utc > {} AND utc < {}'.format(utc_day, utc_day+24*60*60)

    cur.execute(query, ())
    
    return (True,cur.fetchone())


@with_psql
def get_recent_activity(cur, username, n=5):
    apps = ad.get_list(username)[1]
    devs = []
    
    for a in apps:
        devs.append(dd.get_list(a[1])[1])
    
    query = ''
    for a in apps:
        devs = dd.get_list(a[1])
        for d in devs[1]:
            query += """
            (SELECT timedate, appname, devname, data, utc from 
                (SELECT utc, timedate, data from dev_{}_{} limit 5) AS utc, 
                (SELECT '{}' as appname) AS appname,
                (SELECT '{}' as devname) AS devname)
            UNION ALL""".format(a[1],d[1], a[0],d[0])
    query = query[0:-9]
    query += ' ORDER BY utc DESC LIMIT {}'.format(n)
    print(query)

    cur.execute(query, ())

    return (True, cur.fetchall())

