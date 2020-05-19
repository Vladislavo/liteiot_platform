from psycopg2 import sql
from app.helpers.misc import with_psql


# appkeys is a list of tuples [(app1), (app2), ..., (appn)]
# devids is a list of lists of tuples [[(dev1),...],[(dev1),...]]
@with_psql
def get_user_data_count(cur, apps, devs):
    query = 'WITH t AS ('
    i = 0
    for a in apps:
        for d in devs[i]:
           query += """
                SELECT COUNT(*) FROM dev_{}_{} UNION ALL
            """.format(a[1], d[1])
        i += 1
    query += ') SELECT SUM(count) FROM t'

    print(query)
    cur.execute(query, ())
    
    return (True,cur.fetchone())


@with_psql
def get_user_data_count_per_hour(cur, apps, devs, utc_hour):
    query = 'WITH t AS ('
    i = 0
    for a in apps:
        for d in devs[i]:
           query += """
                SELECT COUNT(*) FROM dev_{}_{} UNION ALL
            """.format(a[1], d[1])
        i += 1
    query += ') SELECT SUM(count) FROM t WHERE utc > {} AND utc < {}'.format(utc_hour, utc_hour+60*60)

    print(query)
    cur.execute(query, ())
    
    return (True,cur.fetchone())


@with_psql
def get_user_data_count_per_day(cur, apps, devs, utc_day):
    query = 'WITH t AS ('
    i = 0
    for a in apps:
        for d in devs[i]:
           query += """
                SELECT COUNT(*) FROM dev_{}_{} UNION ALL
            """.format(a[1], d[1])
        i += 1
    query += ') SELECT SUM(count) FROM t WHERE utc > {} AND utc < {}'.format(utc_day, utc_day+24*60*60)

    print(query)
    cur.execute(query, ())
    
    return (True,cur.fetchone())


@with_psql
def get_recent_activity(cur, apps, devs, n):
    query = ''
    i = 0
    for a in apps:
        for d in devs[i]:
            query += """
            (SELECT utc, appname, devname, data from 
                (SELECT utc, data from dev_{}_{} limit 5) AS utc, 
                (SELECT '{}' as appname) AS appname,
                (SELECT {} as devname) AS devname)
            UNION ALL
            """.format( a[1],d[1],
                        a[0],d[0])
       i += 1     
    query = query[0:-9]
    query += 'ORDER BY utc DESC LIMIT 5'
    print(query)

    cur.execute(query, ())

    return (True, cur.fetchall())


