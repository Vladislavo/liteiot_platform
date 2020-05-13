from app.helpers.misc import with_psql
import ast

# expr has a form of list [variable, operand, value]
@with_psql
def create(cur, appkey, devid, nfid, expr):
    res = create_function(appkey, devid, nfid, expr)
    
    if res[0]:
        query = """
        CREATE TRIGGER tr_{}_{}_{}
        AFTER INSERT
        ON dev_{}_{}
        FOR EACH ROW
        EXECUTE PROCEDURE nf_{}_{}_{}()
        """.format( appkey, devid, nfid,
                    appkey, devid,
                    appkey, devid, nfid)

        cur.execute(query)
       
        return (True,)
    return res

@with_psql
def delete(cur, appkey, devid, nfid):
    res = delete_function(appkey, devid, nfid)
    
    if res[0]:
        query = """
        DROP TRIGGER
            tr_{}_{}_{}
        """.format(appkey, devid, nfid)
        
        cur.execute(query)
            
        return (True,)
    return res

# expr has a form of list [variable, operand, value]
@with_psql
def create_function(cur, appkey, devid, nfid, expr):
    query = """
    CREATE OR REPLACE FUNCTION
        nf_{}_{}_{}()
    RETURNS trigger AS
    $BODY$
    BEGIN
    """.format(appkey, devid, nfid)
    
    if expr[1] == 'CHANGES':
        query += """
            INSERT INTO 
                notifications_queue
            VALUES
                ({},{},{})
        """.format(nfid, appkey, devid)
    else:
        query += """
            IF (NEW data->>'{}')::{} {} {} THEN
                INSERT INTO 
                    notifications_queue
                VALUES
                    ({},{},{});
            END IF;
        """.format( expr[0], get_type(expr[2]), expr[1], expr[2]
                    ndif, appkey, devid)
    
    query += """
        RETURN NEW;
    END;
    $BODY$

    LANGUAGE plpgsql VOLATILE
    COST 100;
    """

    print(query)
    cur.execute(query)
        
    return (True, )


@with_psql
def delete_function(cur, appkey, devid, nfid):
    query = """
    DROP FUNCTION nf_{}_{}_{}()
    """.format(appkey, devid, nfid)

    cur.execute(query)

    return (True,)


# python to postgresql type translation
#  int   -> int
#  float -> real
#  bool  -> bool
#  str   -> text
def get_type(tstr):
    tstr = tstr.strip()
    try:
        # int, float, bool
        t = ast.literal_eval(tstr).__name__
    except:
        t = 'text'

    if t == 'float':
        t = 'real'

    return t
