from app.helpers.misc import with_psql
import ast

# expr has a form of list [variable, operand, value]
@with_psql
def create(cur, appkey, devid, nfid):
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

@with_psql
def delete(cur, appkey, devid, nfid):
    query = """
    DROP TRIGGER
        tr_{}_{}_{}
    ON dev_{}_{}
    """.format( appkey, devid, nfid,
                appkey, devid)
    
    cur.execute(query)

    return (True,)

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
    
    query += """
        IF (NEW.data->>'{}')::{} {} {} THEN
            INSERT INTO 
                notifications_queue
            VALUES
                ('{}','{}',{}, now());
        END IF;
    """.format( expr[0], get_type(expr[2]), expr[1], expr[2],
                nfid, appkey, devid)
    
    query += """
        RETURN NEW;
    END;
    $BODY$

    LANGUAGE plpgsql VOLATILE
    COST 100;
    """

    cur.execute(query)
        
    return (True, )


# expr has a form of list [variable, operand, value]
# new listen/notify function
@with_psql
def create_function_rt(cur, appkey, devid, nfid, expr, action_type, action):
    query = """
    CREATE OR REPLACE FUNCTION
        nf_{}_{}_{}()
    RETURNS trigger AS
    $BODY$
    BEGIN
    """.format(appkey, devid, nfid)
    
        #PERFORM pg_notify('nf_channel', '{{"appkey":"{}", "devid":{}, "nfid":"{}", "lvalue":"{}", "op":"{}", "rvalue":"{}", "action_type":"{}", "action":"{}", "message":' || row_to_json(NEW) || '}}');
    query += """
        PERFORM pg_notify('nf_channel', '{{"appkey":"{}", "devid":{}, "nfid":"{}", "lvalue":"{}", "op":"{}", "rvalue":"{}", "action_type":"{}", "action":"{}", "message":' || row_to_json(NEW) || '}}');
    """.format(appkey, devid, nfid, expr[0], expr[1], expr[2], action_type, action)
    
    query += """
        RETURN NEW;
    END;
    $BODY$

    LANGUAGE plpgsql VOLATILE
    COST 100;
    """

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
    if tstr == 'true':
        tstr = 'True'
    elif tstr == 'false':
        tstr = 'False'
    try:
        # int, float, bool
        t = type(ast.literal_eval(tstr)).__name__
    except Exception as e:
        t = 'text'

    if t == 'float':
        t = 'real'

    return t
