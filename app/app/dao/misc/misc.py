from psycopg2 import sql
from app.helpers.misc import with_psql, utc_roundhour, utc_roundday, utc_local_diff
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
    
    if apps != [] and devs != [[]]:
        query = 'WITH t AS ('
        i = 0
        for a in apps:
            for d in devs[i]:
               query += 'SELECT COUNT(*) FROM dev_{}_{} UNION ALL '.format(a[1], d[1])
            i += 1
        query = query[0:-9]
        query += ') SELECT SUM(count) FROM t'
        print(query)
        cur.execute(query, ())
        
        return (True,cur.fetchone())
    else:
        return (True,(0,))


@with_psql
def get_user_data_count_per_hour(cur, username, hour):
    apps = ad.get_list(username)[1]
    devs = []
    
    for a in apps:
        devs.append(dd.get_list(a[1])[1])

    if apps != [] and devs != [[]]:
        utc_hour = utc_roundhour(hour)

        query = 'WITH t AS ('
        i = 0
        for a in apps:
            for d in devs[i]:
               query += 'SELECT utc FROM dev_{}_{} UNION ALL '.format(a[1], d[1])
            i += 1
        query = query[0:-10]
        query += ') SELECT COUNT(*) FROM t WHERE utc > {} AND utc < {}'.format(utc_hour, utc_hour+60*60)

        #print(query)
        cur.execute(query, ())
        
        return (True,cur.fetchone())
    else:
        return (True, (0,))


@with_psql
def get_user_data_count_per_hour_period(cur, username, period):
    apps = ad.get_list(username)[1]
    devs = []
    
    for a in apps:
        devs.append(dd.get_list(a[1])[1])

    if apps != [] and devs != [[]]:
        utc_hour = [utc_roundhour(x) for x in range(period,-1,-1)]
        query = 'WITH t AS ('
        i = 0
        for a in apps:
            for d in devs[i]:
               query += 'SELECT utc FROM dev_{}_{} UNION ALL '.format(a[1], d[1])
            i += 1
        query = query[0:-10]
        query += ') SELECT * FROM ('
        for uh in utc_hour:
            query +=' SELECT COUNT(*) FROM t WHERE utc > {} AND utc < {} UNION ALL'.format(uh, uh+60*60)
        query = query[0:-9]
        query += ') w'

        cur.execute(query, ())
        
        return (True,cur.fetchall())
    else:
        return (True, [(0,)])



@with_psql
def get_user_data_count_per_day(cur, username, day=0):
    apps = ad.get_list(username)[1]
    devs = []
    
    for a in apps:
        devs.append(dd.get_list(a[1])[1])

    if apps != [] and devs != [[]]:
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
    else:
        return (True, (0,))


@with_psql
def get_user_data_count_per_day_period(cur, username, period):
    apps = ad.get_list(username)[1]
    devs = []
    
    for a in apps:
        devs.append(dd.get_list(a[1])[1])

    if apps != [] and devs != [[]]:
        utc_hour = [utc_roundday(x) for x in range(period,-1,-1)]

        query = 'WITH t AS ('
        i = 0
        for a in apps:
            for d in devs[i]:
               query += 'SELECT utc FROM dev_{}_{} UNION ALL '.format(a[1], d[1])
            i += 1
        query = query[0:-10]
        query += ') SELECT * FROM ('
        for uh in utc_hour:
            query +=' SELECT COUNT(*) FROM t WHERE utc > {} AND utc < {} UNION ALL'.format(uh, uh+24*60*60)
        query = query[0:-9]
        query += ') w'

        cur.execute(query, ())
        
        return (True,cur.fetchall())
    else:
        return (True, [(0,)])


@with_psql
def get_recent_activity(cur, username, n=5):
    apps = ad.get_list(username)[1]
    devs = []
    
    for a in apps:
        devs.append(dd.get_list(a[1])[1])
    
    if apps != [] and devs != [[]]:
        query = ''
        for a in apps:
            devs = dd.get_list(a[1])
            for d in devs[1]:
                query += """
                (SELECT timedate, appname, devname, data, utc, appkey, devid from 
                    (SELECT utc, timedate, data from dev_{}_{} ORDER BY utc DESC limit 5) AS utc, 
                    (SELECT '{}' as appname) AS appname,
                    (SELECT '{}' as appkey) AS appkey,
                    (SELECT '{}' as devid) AS devid,
                    (SELECT '{}' as devname) AS devname)
                UNION ALL""".format(a[1],d[1], a[0],a[1], d[1],d[0])
        query = query[0:-9]
        query += ' ORDER BY utc DESC LIMIT {}'.format(n)

        cur.execute(query, ())

        return (True, cur.fetchall())
    else:
        return (True, [])


