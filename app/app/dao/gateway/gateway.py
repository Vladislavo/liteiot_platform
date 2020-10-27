from app.helpers.misc import with_psql
from psycopg2 import Binary

@with_psql
def create(cur, name, gwid, protocol, desc, secure_key, telemetry_send_freq):
    cur.execute(
        'INSERT INTO gateways VALUES (%s, %s, %s, %s, %s, %s)',
        (name, gwid, protocol, desc, secure_key, telemetry_send_freq)
    )

    return (True,)


@with_psql
def get(cur, gwid):
    cur.execute('SELECT row_to_json(r) FROM (SELECT * FROM gateways WHERE id = %s) r', gwid)

    return (True, cur.fetchone()[0][0])


@with_psql
def get_all(cur):
    cur.execute('SELECT row_to_json(r) FROM (SELECT * FROM gateways) r')

    gws = cur.fetchall()

    return (True, [gw[0] for gw in gws])


@with_psql
def delete(cur, gwid):
    cur.execute('DELETE FROM gateways WHERE id = %s', gwid)

    return (True,)


@with_psql
def update(cur, name, gwid, protocol, desc, telemetry_send_freq):
    cur.execute(
        """
            UPDATE 
                gateways
            SET
                name = %s,
                protocol = %s,
                desc = %s,
                telemetry_send_freq = %s
            WHERE
                id = %s
        """,
        (name, protocol, desc, telemetry_send_freq, gwid)
    )
    return (True,)

