import os
import time
import json
import logging
import mysql.connector

from flask import current_app, session

from app import utility
# python 2 vs 3
from app import logger


# import commander.logger as logger


def query_database(sql, db_creds=None, tries=2):
    """
    Runs queries against target database.

    Args: sql(string), variables(dict), tries(int)
    Returns: results(list(dicts))
    """
    logger.Log('FUNCTION CALL: query_database()', logging.DEBUG)
    for i in range(tries):
        try:
            if db_creds:
                conn = mysql.connector.connect(user=db_creds['DB_USER'], password=db_creds['DB_PASS'],
                                               host=db_creds['DB_HOST'], database=db_creds['DB_NAME'])
            else:
                # conn = mysql.connector.connect(user=current_app.config['DB_USER'],
                #                                password=current_app.config['DB_PASS'],
                #                                host=current_app.config['DB_HOST'],
                #                                database=current_app.config['DB_NAME'])
                conn = mysql.connector.connect(user=os.environ.get('MYSQL_DATABASE_USER'),
                                               password=os.environ.get('MYSQL_DATABASE_PASSWORD'),
                                               host=os.environ.get('MYSQL_DATABASE_HOST'),
                                               database=os.environ.get('MYSQL_DATABASE_DB'),
                                               port=os.environ.get('MYSQL_DATABASE_PORT'))
            cursor = conn.cursor(dictionary=True)

            print("MYSQL for OPS MANAGER has connected.")
            print("SQL: ",sql)
            cursor.execute(sql)
            if sql.upper().startswith('INSERT'):
                result = cursor.lastrowid
                conn.commit()
            elif sql.upper().startswith('UPDATE') or sql.upper().startswith('DELETE'):
                conn.commit()
                result = None
            elif sql.upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                result = None

            cursor.close()
            conn.close()

            return result

        except Exception as e:
            time.sleep(10)
            logger.Log('retry attempt: %s' % (i + 1), logging.WARN)
            if i < tries - 1:
                logger.Log('failed to connect to target database or execute query.',logging.WARN)
                logger.Log('attempted query: \n\n%s\n\n' % sql, logging.WARN)
                continue
            else:
                raise
            break


# User

def user_get_group_by_username(username):
    logger.Log('FUNCTION CALL: user_get_group_by_username()', logging.DEBUG)

    sql = """SELECT `ops_man_ldap_user`.`id`, `ops_man_ldap_user`.`username`, `ops_man_ldap_user`.`password`, `ops_man_ldap_group`.`id`, `ops_man_ldap_group`.`name`
        FROM `ops_man_ldap_user`, `ops_man_ldap_group` 
        WHERE `ops_man_ldap_group`.`id` = `ops_man_ldap_user`.`ops_man_ldap_group`
        AND `ops_man_ldap_user`.`username` = '%s';""" % (username)

    logger.Log('user_get_group_by_username: \n\n%s\n\n' % sql, logging.DEBUG)
    group = query_database(sql)[0]
    return group


def get_all_groups_for_form():
    logger.Log('FUNCTION CALL: get_all_groups_for_form()', logging.DEBUG)
    sql = """SELECT `id`, `name` FROM `ops_man_ldap_group`;"""
    logger.Log('get_all_groups_for_form: \n\n%s\n\n' % sql, logging.DEBUG)

    user_groups = query_database(sql)
    user_groups_dd = [(item['id'], item['name']) for item in user_groups]

    return user_groups_dd


def get_all_environments_for_form():
    logger.Log('FUNCTION CALL: get_all_environments_for_form()', logging.DEBUG)
    sql = """SELECT `id`, `name` FROM `ops_man_environment`;"""
    logger.Log('get_all_environments_for_form: \n\n%s\n\n' % sql, logging.DEBUG)

    environments = query_database(sql)
    environments_dd = [(item['id'], item['name']) for item in environments]

    return environments_dd


def get_all_datacenters_for_form():
    logger.Log('FUNCTION CALL: get_all_datacenters_for_form()', logging.DEBUG)
    sql = """SELECT `id`, `name` FROM `ops_man_datacenter`;"""
    logger.Log('get_all_datacenters_for_form: \n\n%s\n\n' % sql, logging.DEBUG)

    datacenters = query_database(sql)
    datacenters_dd = [(item['id'], item['name']) for item in datacenters]

    return datacenters_dd


def user_create_full(user):
    logger.Log('FUNCTION CALL: user_create_full()', logging.DEBUG)
    title, name, email, username, linux_user_id, department, security_group = (
    user['title'], 
    user['name'], 
    user['email'], 
    user['username'], 
    user['linux_user_id'], 
    user['department'], 
    user['security_group'], 
)
    sql = """INSERT INTO `ops_man_ldap_user` (`username`, `email`, `title`,`name`, password, linux_user_id, department,ops_man_ldap_group) 
    VALUES ('%s', '%s', '%s','%s', '%s',%s,'%s',%s)""" %(username, email.lower(), title, name, "qw2er14", linux_user_id, department, security_group)
    logger.Log('user_create_full: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def user_create(username, title, name, email, password, password_expiry_at):
    logger.Log('FUNCTION CALL: user_create()', logging.DEBUG)
    sql = """INSERT INTO `ops_man_ldap_user` (`username`, `email`, `title`, `name`, `password`, `password_expiry_at`) VALUES ('%s', '%s', '%s', '%s', '%s', '%s')""" % (username, email.lower(), title, name, password, password_expiry_at)
    logger.Log('user_create: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)

def user_create_partial(username, password, password_expiry_at):
    logger.Log('FUNCTION CALL: user_create_partial()', logging.DEBUG)
    sql = """INSERT INTO `ops_man_ldap_user` (`username`, `password`, `password_expiry_at`) VALUES ('%s', '%s', '%s')""" % (username, password, password_expiry_at)
    logger.Log('user_create_partial: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def tenant_create(service_id, name, linux_username, linux_uid, is_disabled):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """INSERT INTO `ops_man_tenant` (`name`, `service_id`, `linux_username`, `linux_uid`, `is_disabled`) VALUES ('%s', '%s', '%s', '%s', '%s')""" % (name, service_id, linux_username, linux_uid, is_disabled)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)


def tenant_attributes_type_create(name, limit):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """INSERT INTO `ops_man_tenant_attribute_type` (`name`, `limit`) VALUES ('%s', '%s')""" % (name, limit)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)


def tenant_attributes_type_update(id,limit, attribute_name):
    logger.Log('FUNCTION CALL: tenant_attributes_type_update()', logging.DEBUG)
    sql = """UPDATE `ops_man_tenant_attribute_type` set `limit` = %s, `name` = '%s' WHERE id = %s""" % (limit, attribute_name, id)
    logger.Log('tenant_attributes_type_update: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)


def user_attributes_type_create(name, limit):
    logger.Log('FUNCTION CALL: user_attributes_type_create()', logging.DEBUG)
    sql = """INSERT INTO `ops_man_ldap_user_attribute_type` (`name`, `limit`) VALUES ('%s', '%s')""" % (name, limit)
    logger.Log('user_attributes_type_create: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)


def user_attributes_type_update(id,limit, name):
    logger.Log('FUNCTION CALL: user_attributes_type_update()', logging.DEBUG)
    sql = """UPDATE `ops_man_ldap_user_attribute_type` set `limit` = %s, `name` = '%s' WHERE id = %s""" % (limit,name,id)
    logger.Log('user_attributes_type_update: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)


def user_attributes_type_delete(id):
    logger.Log('FUNCTION CALL: user_attributes_type_delete()', logging.DEBUG)
    sql = """DELETE FROM `ops_man_ldap_user_attribute_type` WHERE id = %s""" % (id)
    logger.Log('user_attributes_type_delete: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)


def get_mysql_password_hash(password):
    logger.Log('FUNCTION CALL: get_mysql_password_hash()', logging.DEBUG)
    sql = """SELECT CONCAT('*', UPPER(SHA1(UNHEX(SHA1('%s'))))) as hashed_password""" %password
    logger.Log('get_mysql_password_hash: \n\n%s\n\n' % sql, logging.DEBUG)
    return query_database(sql)[0]['hashed_password']


def check_user_attribute_exist(user_id,attribute_id):
    logger.Log('FUNCTION CALL: check_user_attribute_exist()', logging.DEBUG)
    sql = """SELECT 1 FROM ops_man_ldap_user_attribute 
            WHERE ops_man_ldap_user_id = %s 
            and ops_man_ldap_user_attribute_type_id = (Select id FROM ops_man_ldap_user_attribute_type where id = %s LIMIT 1)""" %(user_id, attribute_id)
    logger.Log('check_user_attribute_exist: \n\n%s\n\n' % sql, logging.DEBUG)

    if(len(query_database(sql)) > 0):
        return True
    return False


def check_user_attribute_exist_by_name(user_id,attribute_name):
    logger.Log('FUNCTION CALL: check_user_attribute_exist()', logging.DEBUG)
    sql = """SELECT 1 FROM ops_man_ldap_user_attribute 
            WHERE ops_man_ldap_user_id = %s 
            and ops_man_ldap_user_attribute_type_id = (Select id FROM ops_man_ldap_user_attribute_type where name = '%s' LIMIT 1)""" %(user_id, attribute_name)
    logger.Log('check_user_attribute_exist: \n\n%s\n\n' % sql, logging.DEBUG)

    if(len(query_database(sql)) > 0):
        return True
    return False


def check_user_attribute_type_exist_by_name(attribute_name):
    logger.Log('FUNCTION CALL: check_user_attribute_type_exist_by_name()', logging.DEBUG)
    sql = """Select 1 FROM ops_man_ldap_user_attribute_type where name = '%s' LIMIT 1""" %(attribute_name)
    logger.Log('check_user_attribute_type_exist_by_name: \n\n%s\n\n' % sql, logging.DEBUG)

    if(len(query_database(sql)) > 0):
        return True
    return False


def Update_user_attribute_by_id(user_attribute_id, attribute_value):
    logger.Log('FUNCTION CALL: Update_user_attribute_by_id()', logging.DEBUG)
    sql = """update ops_man_ldap_user_attribute set `value` = '%s' where `id` = %s """ %(attribute_value, user_attribute_id)
    logger.Log('Update_user_attribute_by_id: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def delete_user_attribute_by_id(user_attribute_id):
    logger.Log('FUNCTION CALL: delete_user_attribute_by_id()', logging.DEBUG)
    sql = """DELETE FROM ops_man_ldap_user_attribute where `id` = %s """ %(user_attribute_id)
    logger.Log('delete_user_attribute_by_id: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def Update_user_attribute(user_id, attribute_id, attribute_value):
    logger.Log('FUNCTION CALL: Update_user_attribute()', logging.DEBUG)
    sql = """update ops_man_ldap_user_attribute 
            set value = '%s' 
            where ops_man_ldap_user_id = %s 
            and ops_man_ldap_user_attribute_type_id = (Select id FROM ops_man_ldap_user_attribute_type where id = %s LIMIT 1)""" %(attribute_value, user_id, attribute_id)
    logger.Log('Update_user_attribute: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def add_user_attribute(user_id, attribute_id, attribute_value):
    logger.Log('FUNCTION CALL: add_user_attribute()', logging.DEBUG)
    sql = """INSERT INTO ops_man_ldap_user_attribute(ops_man_ldap_user_id, ops_man_ldap_user_attribute_type_id, value) 
                VALUES(%s, %s, '%s');""" %(user_id, attribute_id, attribute_value)
    logger.Log('add_user_attribute: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def add_user_attribute_by_name(user_id, attribute_name, attribute_value):
    logger.Log('FUNCTION CALL: Update_user_attribute()', logging.DEBUG)
    sql = """INSERT INTO ops_man_ldap_user_attribute(ops_man_ldap_user_id, ops_man_ldap_user_attribute_type_id, value) 
                VALUES(%s, (Select id FROM ops_man_ldap_user_attribute_type where name = '%s' LIMIT 1), '%s');""" %(user_id, attribute_name, attribute_value)
    logger.Log('Update_user_attribute: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def Update_user_attribute_by_name(user_id, attribute_name, attribute_value):
    logger.Log('FUNCTION CALL: add_user_attribute()', logging.DEBUG)
    sql = """update ops_man_ldap_user_attribute 
            set value = '%s' 
            where ops_man_ldap_user_id = %s 
            and ops_man_ldap_user_attribute_type_id = (Select id FROM ops_man_ldap_user_attribute_type where name = '%s' LIMIT 1)""" %(attribute_value, user_id, attribute_name)
    logger.Log('add_user_attribute: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def get_user_attribute_type_by_id(attribute_id):
    logger.Log('FUNCTION CALL: get_user_attribute_type_by_id()', logging.DEBUG)
    sql = """select * from `ops_man_ldap_user_attribute_type` where id = %s;""" %(attribute_id)
    logger.Log('get_user_attribute_type_by_id: \n\n%s\n\n' % sql, logging.DEBUG)

    if(len(query_database(sql)) > 0):
        return query_database(sql)[0]
    return None


def get_user_attribute_count(user_id, attribute_id):
    logger.Log('FUNCTION CALL: get_user_attribute_count()', logging.DEBUG)
    sql = """select COUNT(1) as `user_attribute_count` from `ops_man_ldap_user_attribute` a
    JOIN `ops_man_ldap_user_attribute_type` b on a.ops_man_ldap_user_attribute_type_id = b.id
    WHERE a.ops_man_ldap_user_id = %s and b.id = %s;""" %(user_id, attribute_id)
    logger.Log('get_user_attribute_count: \n\n%s\n\n' % sql, logging.DEBUG)

    return query_database(sql)[0]


def get_all_user_attribute_by_group_id(group_id):
    logger.Log('FUNCTION CALL: get_all_user_attribute_by_group_id()', logging.DEBUG)
    sql = """select a.*, b.`name` as attribute_name, u.id as user_id from `ops_man_ldap_user_attribute` a
            JOIN `ops_man_ldap_user_attribute_type` b on a.ops_man_ldap_user_attribute_type_id = b.id
            JOIN `ops_man_ldap_user` u on u.id = a.ops_man_ldap_user_id
            JOIN `ops_man_ldap_group` g on g.id = u.ops_man_ldap_group
            WHERE g.id = %s;""" %(group_id)
    logger.Log('get_all_user_attribute_by_group_id: \n\n%s\n\n' % sql, logging.DEBUG)
    return query_database(sql)
    

def tenant_attribute_create(ops_man_tenant_id, ops_man_tenant_attribute_type_id, value):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """INSERT INTO `ops_man_tenant_attribute` (`ops_man_tenant_id`, `ops_man_tenant_attribute_type_id`, `value`) VALUES ('%s', '%s', '%s')""" % (ops_man_tenant_id, ops_man_tenant_attribute_type_id, value)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)

def get_tenant_attribute_count(tenant_id, attribute_id):
    logger.Log('FUNCTION CALL: get_tenant_attribute_count()', logging.DEBUG)
    sql = """select COUNT(1) as `tenant_attribute_count` from `ops_man_tenant_attribute` a
    JOIN `ops_man_tenant_attribute_type` b on a.ops_man_tenant_attribute_type_id = b.id
    WHERE a.ops_man_tenant_id = %s and b.id = %s;""" %(tenant_id, attribute_id)
    logger.Log('get_tenant_attribute_count: \n\n%s\n\n' % sql, logging.DEBUG)

    return query_database(sql)[0]


def get_tenant_attribute_type_by_id(attribute_id):
    logger.Log('FUNCTION CALL: get_tenant_attribute_type_by_id()', logging.DEBUG)
    sql = """select * from `ops_man_tenant_attribute_type` WHERE id = %s;""" %(attribute_id)
    logger.Log('get_tenant_attribute_type_by_id: \n\n%s\n\n' % sql, logging.DEBUG)

    if(len(query_database(sql)) > 0):
        return query_database(sql)[0]
    return None
    

def datacenter_create(name):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """INSERT INTO `ops_man_datacenter` (`name`) VALUES ('%s')""" % (name)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)


def environment_create(name):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """INSERT INTO `ops_man_environment` (`name`) VALUES ('%s')""" % (name)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)


def group_create(name, linux_group_id, linux_group_name, is_admin, is_admin_tenant):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """INSERT INTO `ops_man_ldap_group` (`name`, `linux_group_name`, `linux_group_id`, `is_admin`, `is_admin_tenant`) VALUES ('%s', '%s', '%s', %s, %s)""" % (name, linux_group_name, linux_group_id, is_admin, is_admin_tenant)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)

def group_delete(id):
    logger.Log('FUNCTION CALL: group_delete()', logging.DEBUG)
    before_data = get_group_by_id(id)
    sql = """DELETE FROM `ops_man_ldap_group` where `id` = %s""" % (id)
    query_database(sql)
    create_history(session['username'], 'delete group', before_data.get('name'), {'before': before_data,  'after': None})
    logger.Log('group_delete: \n\n%s\n\n' % sql, logging.DEBUG)


def get_group_by_id(id):
    logger.Log('FUNCTION CALL: get_admin_by_id()', logging.DEBUG)
    sql = """Select * from `ops_man_ldap_group` where `id` = %s""" % (id)
    logger.Log('get_admin_by_id: \n\n%s\n\n' % sql, logging.DEBUG)
    data = query_database(sql)
    if len(data) > 0:
        return data[0]
    return None
    

def Update_group_privilege(id, is_admin):
    logger.Log('FUNCTION CALL: Update_group_privilege()', logging.DEBUG)
    before_data = get_group_by_id(id)
    sql = """update `ops_man_ldap_group` set `is_admin` = %s where `id` = %s""" % (is_admin,id)
    query_database(sql)
    after_data = get_group_by_id(id)
    create_history(session['username'], 'edit group', before_data.get('name'), {'before': before_data,  'after': after_data})

    logger.Log('Update_group_privilege: \n\n%s\n\n' % sql, logging.DEBUG)

def Update_group_is_admin_tenant(id, is_admin_tenant):
    logger.Log('FUNCTION CALL: Update_group_privilege()', logging.DEBUG)
    before_data = get_group_by_id(id)
    sql = """update `ops_man_ldap_group` set `is_admin_tenant` = %s where `id` = %s""" % (is_admin_tenant, id)
    query_database(sql)
    after_data = get_group_by_id(id)
    create_history(session['username'], 'edit group', before_data.get('name'), {'before': before_data,  'after': after_data})

    logger.Log('Update_group_privilege: \n\n%s\n\n' % sql, logging.DEBUG)



def get_tenant_by_id(id):    
    logger.Log('FUNCTION CALL: get_tenant_by_id()', logging.DEBUG)
    sql = """Select * from `ops_man_tenant` where `id` = %s""" % (id)
    logger.Log('get_tenant_by_id: \n\n%s\n\n' % sql, logging.DEBUG)
    data = query_database(sql)
    if len(data) > 0:
        return data[0]
    return None


def Update_tenant_is_disable(id, is_disabled):
    logger.Log('FUNCTION CALL: Update_tenant_is_disable()', logging.DEBUG)
    before_data = get_tenant_by_id(id)
    sql = """update `ops_man_tenant` set `is_disabled` = %s where `id` = %s""" % (is_disabled, id)
    query_database(sql)
    after_data = get_tenant_by_id(id)
    create_history(session['username'], 'edit tenant', before_data.get('name'), {'before': before_data,  'after': after_data})
    logger.Log('Update_tenant_is_disable: \n\n%s\n\n' % sql, logging.DEBUG)


def Update_tenant_sftp_status(id, sftp_status):
    logger.Log('FUNCTION CALL: Update_tenant_is_disable()', logging.DEBUG)
    before_data = get_tenant_by_id(id)
    sql = """update `ops_man_tenant` set `is_sftp` = %s where `id` = %s""" % (sftp_status, id)
    query_database(sql)
    after_data = get_tenant_by_id(id)
    create_history(session['username'], 'edit tenant', before_data.get('name'), {'before': before_data,  'after': after_data})
    logger.Log('Update_tenant_is_disable: \n\n%s\n\n' % sql, logging.DEBUG)

def group_update(id, name, linux_group_name, linux_group_id):
    logger.Log('FUNCTION CALL: group_update()', logging.DEBUG)
    before_data = get_group_by_id(id)
    sql = """update `ops_man_ldap_group` set `name` = '%s', linux_group_name = '%s', linux_group_id = %s where `id` = %s""" % (name, linux_group_name, linux_group_id, id)
    query_database(sql)
    after_data = get_group_by_id(id)
    create_history(session['username'], 'edit group', before_data.get('name'), {'before': before_data,  'after': after_data})
    logger.Log('group_update: \n\n%s\n\n' % sql, logging.DEBUG)

    


def user_delete_by_id(user_id, request_by=""):
    logger.Log('FUNCTION CALL: user_delete_by_id()', logging.DEBUG)
    before_data = get_user_by_id(user_id)
    sql = """DELETE FROM `ops_man_ldap_user` WHERE `id` = %s""" % (user_id)

    create_history(session['username'], 'delete user', before_data[0].get('username'), {'before': before_data,  'after': None})
    logger.Log('user_delete_by_id: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def user_validate(field, value):
    logger.Log('FUNCTION CALL: user_validate()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_ldap_user` WHERE `%s` = '%s'""" % (field, value)
    logger.Log('user_validate: \n\n%s\n\n' % sql, logging.DEBUG)
    exists = query_database(sql)

    if exists:
        return True
    else:
        return False

def get_user_by_id(user_id):
    return query_database("""Select * from `ops_man_ldap_user` where `id` = %s""" % (user_id))

def user_update_by_id(username, user_id, request_by=""):
    logger.Log('FUNCTION CALL: user_update_by_id()', logging.DEBUG)
    
    before_data = get_user_by_id(user_id)
    sql = """UPDATE `ops_man_ldap_user` SET `username` = '%s', WHERE `id` = %s""" % (username, user_id)
    query_database(sql)
    after_data = get_user_by_id(user_id)
    create_history(session['username'], 'edit user', after_data[0].get('username'), {'before': before_data,  'after': after_data})
    logger.Log('user_update_by_id: \n\n%s\n\n' % sql, logging.DEBUG)


def user_edit_by_id(user_id, linux_user_id, department, security_group_id, request_by=""):
    logger.Log('FUNCTION CALL: user_edit_by_id()', logging.DEBUG)
    before_data = get_user_by_id(user_id)
    
    sql = """UPDATE `ops_man_ldap_user` SET `linux_user_id` = %s, department = '%s', ops_man_ldap_group = %s WHERE `id` = %s""" % (linux_user_id, department, security_group_id, user_id)
    query_database(sql)

    after_data = get_user_by_id(user_id)
    create_history(session['username'], 'edit user', after_data[0].get('username'), {'before': before_data,  'after': after_data})
    logger.Log('user_edit_by_id: \n\n%s\n\n' % sql, logging.DEBUG)


def user_update_password_by_id(password, user_id):
    logger.Log('FUNCTION CALL: user_update_password_by_id()', logging.DEBUG)
    before_data = get_user_by_id(user_id)

    sql = """UPDATE `ops_man_ldap_user` SET `password` = '%s' WHERE `id` = %s""" % (password, user_id)
    query_database(sql)

    after_data = get_user_by_id(user_id)
    create_history(session['username'], 'edit user', after_data[0].get('username'), {'before': before_data,  'after': after_data})
    logger.Log('user_update_password_by_id: \n\n%s\n\n' % sql, logging.DEBUG)


def user_update_password_and_time_by_id(password, user_id, password_expiry_at):
    logger.Log('FUNCTION CALL: user_update_password_and_time_by_id()', logging.DEBUG)
    before_data = get_user_by_id(user_id)

    sql = """UPDATE `ops_man_ldap_user` SET `password` = '%s', password_expiry_at = '%s' WHERE `id` = %s""" % (password, password_expiry_at, user_id)
    query_database(sql)

    after_data = get_user_by_id(user_id)
    username = 'anonymous'
    if session and session.get('username'):
        username = session.get('username')

    create_history(username, 'edit user', after_data[0].get('username'), {'before': before_data,  'after': after_data})
    logger.Log('user_update_password_and_time_by_id: \n\n%s\n\n' % sql, logging.DEBUG)

def user_get_by_username(username):
    logger.Log('FUNCTION CALL: user_get_by_username()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_ldap_user` WHERE `username` = '%s'""" % (username)
    logger.Log('user_get_by_username: \n\n%s\n\n' % sql, logging.DEBUG)
    if(len(query_database(sql)) > 0):
        return query_database(sql)[0]
    return None

def user_by_email(email):
    logger.Log('FUNCTION CALL: user_get_by_username()', logging.DEBUG)
    sql = """SELECT `id`, `username`, `password`, LOWER(`email`) FROM `ops_man_ldap_user` WHERE LOWER(`email`) = '%s'""" % (email.lower())
    logger.Log('user_get_by_username: \n\n%s\n\n' % sql, logging.DEBUG)
    
    if(len(query_database(sql)) > 0):
        return query_database(sql)[0]
    return None


def user_get_by_id(user_id):
    logger.Log('FUNCTION CALL: user_get_by_id()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_ldap_user` WHERE `id` = %s""" % (user_id)
    logger.Log('user_get_by_id: \n\n%s\n\n' % sql, logging.DEBUG)
    user = query_database(sql)
    if(user and len(user) > 0):
        return user[0]
    return None


def user_get_all():
    logger.Log('FUNCTION CALL: user_get_all()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_ldap_user`"""
    logger.Log('user_get_all: \n\n%s\n\n' % sql, logging.DEBUG)
    data_users = query_database(sql)
    return data_users

def user_get_all_with_group():
    logger.Log('FUNCTION CALL: user_get_all_with_group()', logging.DEBUG)
    sql = """SELECT a.*, ifnull(b.`name`, '')  as 'group_name' FROM `ops_man_ldap_user` a 
            LEFT JOIN `ops_man_ldap_group` b on a.ops_man_ldap_group = b.id"""
    logger.Log('user_get_all_with_group: \n\n%s\n\n' % sql, logging.DEBUG)
    data_users = query_database(sql)
    return data_users

def user_get_paginated(start_index, total_items):
    logger.Log('FUNCTION CALL: user_get_paginated()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_ldap_user` LIMIT %s, %s""" %(start_index, total_items)
    logger.Log('user_get_paginated: \n\n%s\n\n' % sql, logging.DEBUG)
    data_users = query_database(sql)
    return data_users


# groups
def group_get_all():
    logger.Log('FUNCTION CALL: group_get_all()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_ldap_group`"""
    logger.Log('group_get_all: \n\n%s\n\n' % sql, logging.DEBUG)
    data_groups = query_database(sql)
    return data_groups


def users_get_by_group_id(group_id):
    logger.Log('FUNCTION CALL: users_get_by_group_id()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_ldap_user` where ops_man_ldap_group = %s""" % (group_id)
    logger.Log('users_get_by_group_id: \n\n%s\n\n' % sql, logging.DEBUG)
    return query_database(sql)

def user_get_all_with_group_by_group_id(group_id):
    logger.Log('FUNCTION CALL: user_get_all_with_group_by_group_id()', logging.DEBUG)
    sql = """SELECT a.*, ifnull(b.`name`, '')  as 'group_name' FROM `ops_man_ldap_user` a 
            LEFT JOIN `ops_man_ldap_group` b on a.ops_man_ldap_group = b.id where ops_man_ldap_group = %s""" % (group_id)
    logger.Log('user_get_all_with_group_by_group_id: \n\n%s\n\n' % sql, logging.DEBUG)
    data_users = query_database(sql)
    return data_users


def get_user_attributes_by_user_id(user_id):
    logger.Log('FUNCTION CALL: get_user_attributes()', logging.DEBUG)
    sql = """select a.*, b.`name` as `attribute_name`, 
            CASE WHEN b.name IN ('password_linux', 'password_mysql', 'password_svn') THEN 1 ELSE 0 END AS `system_ind`
            from ops_man_ldap_user_attribute a 
            join ops_man_ldap_user_attribute_type b on a.ops_man_ldap_user_attribute_type_id = b.id
            where a.ops_man_ldap_user_id = %s
            order by a.id""" %(user_id)
    logger.Log('get_user_attributes: \n\n%s\n\n' % sql, logging.DEBUG)
    return query_database(sql)


def group_get_by_id(id):
    logger.Log('FUNCTION CALL: group_get_by_name()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_ldap_group` WHERE `id` = %s""" % (id)
    logger.Log('group_get_by_name: \n\n%s\n\n' % sql, logging.DEBUG)
    group = query_database(sql)
    if(group and len(group) > 0):
        return group[0]
    return None


def get_all_permission_matrix():
    logger.Log('FUNCTION CALL: get_all_permission_matrix()', logging.DEBUG)
    sql = """select * from `ops_man_permission_matrix`"""
    logger.Log('get_all_permission_matrix: \n\n%s\n\n' % sql, logging.DEBUG)
    try:
        return query_database(sql)
    except Exception as e:
        return None


def create_permission_matrix(group_id, environment_id, datacenter_id):
    logger.Log('FUNCTION CALL: create_permission_matrix()', logging.DEBUG)
    sql = """INSERT INTO `ops_man_permission_matrix`(`ops_man_datacenter_id`, `ops_man_environment_id`, `ops_man_ldap_group_id`)
            VALUES(%s, %s, %s) """ %(datacenter_id, environment_id, group_id) 
    logger.Log('create_permission_matrix: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def permission_matrix_delete(permission_id):
    logger.Log('FUNCTION CALL: permission_matrix_delete()', logging.DEBUG)
    sql = """DELETE FROM `ops_man_permission_matrix` where id = %s""" %(permission_id) 
    logger.Log('permission_matrix_delete: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def is_valid_permission(group_id, environment_id, datacenter_id):
    logger.Log('FUNCTION CALL: is_valid_permission()', logging.DEBUG)
    sql = """select 1 as permission_exists from ops_man_permission_matrix where ops_man_datacenter_id = %s and ops_man_environment_id = %s and ops_man_ldap_group_id = %s""" %(datacenter_id, environment_id, group_id) 
    logger.Log('is_valid_permission: \n\n%s\n\n' % sql, logging.DEBUG)
    if(len(query_database(sql)) > 0):
        return False
    else: 
        return True


# Tenant
def tenant_get_all():
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_tenant`"""
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    data_tenants = query_database(sql)

    return data_tenants


def validate_tenant_on_creation(linux_uid, linux_username, name, service_id):
    validations = {
        'linux_uid_UNIQUE': ("""SELECT 1 FROM ops_man_tenant WHERE linux_uid = %s""" % (linux_uid), "Linux UID already exists."),
        'linux_username_UNIQUE': (
        """SELECT 1 FROM ops_man_tenant WHERE linux_username = '%s'""" % (linux_username), "Linux Username already exists."),
        'name_UNIQUE': ("""SELECT 1 FROM ops_man_tenant WHERE name = '%s'""" % (name), "Name already exists."),
        'service_id_UNIQUE': (
        """SELECT 1 FROM ops_man_tenant WHERE service_id = %s""" % (service_id), "Service ID already exists.")
    }

    # Iterate over validations and execute queries
    for key, (query, message) in validations.items():
        if query_database(query):
            return False, message  # Return False and the corresponding message if a validation fails

    return True, "All validations passed."  # Return True and a success message if all validations pass


def tenant_attributes_types_get_all():
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_tenant_attribute_type`"""
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    data_tenant_attributes = query_database(sql)

    return data_tenant_attributes

def user_attributes_types_get_all():
    logger.Log('FUNCTION CALL: user_attributes_types_get_all()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_ldap_user_attribute_type`"""
    logger.Log('user_attributes_types_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    return query_database(sql)

def get_user_attribute_for_select():
    logger.Log('FUNCTION CALL: get_user_attribute_for_select()', logging.DEBUG)
    sql = """SELECT `id` as id, `name` FROM `ops_man_ldap_user_attribute_type`"""
    logger.Log('get_user_attribute_for_select: \n\n%s\n\n' % sql, logging.DEBUG)

    user_attributes = query_database(sql)
    return [(item['id'], item['name']) for item in user_attributes]    


def get_tenant_attributes(tenant_id):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """SELECT a.*, b.`name` as `attribute_name` FROM `ops_man_tenant_attribute` a
            JOIN `ops_man_tenant_attribute_type` b on a.ops_man_tenant_attribute_type_id = b.id
            WHERE a.`ops_man_tenant_id` = %s""" % (tenant_id)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    data_tenant_attributes = query_database(sql)
    return data_tenant_attributes

def get_tenant_attribute_by_id(ta_id):
    logger.Log('FUNCTION CALL: get_tenant_attribute_by_id()', logging.DEBUG)
    sql = """SELECT a.*, b.`name` as `attribute_name` FROM `ops_man_tenant_attribute` a
            JOIN `ops_man_tenant_attribute_type` b on a.ops_man_tenant_attribute_type_id = b.id
            WHERE a.`id` = %s""" % (ta_id)
    logger.Log('get_tenant_attribute_by_id: \n\n%s\n\n' % sql, logging.DEBUG)

    data_tenant_attributes = query_database(sql)
    if(len(data_tenant_attributes)> 0):
        return data_tenant_attributes[0]
    return None


def get_user_attribute_by_id(ua_id):
    logger.Log('FUNCTION CALL: get_user_attribute_by_id()', logging.DEBUG)
    sql = """SELECT a.*, b.`name` as `attribute_name` FROM `ops_man_ldap_user_attribute` a
            JOIN `ops_man_ldap_user_attribute_type` b on a.ops_man_ldap_user_attribute_type_id = b.id
            WHERE a.`id` = %s""" % (ua_id)
    logger.Log('get_user_attribute_by_id: \n\n%s\n\n' % sql, logging.DEBUG)

    data_user_attributes = query_database(sql)
    if(len(data_user_attributes)> 0):
        return data_user_attributes[0]
    return None


def update_tenant_attributes_by_id(attribute_id, value):
    logger.Log('FUNCTION CALL: update_tenant_attributes_by_id()', logging.DEBUG)
    sql = """UPDATE `ops_man_tenant_attribute` SET `value` = '%s' WHERE id = %s""" % (value, attribute_id)
    logger.Log('update_tenant_attributes_by_id: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)


def delete_tenant_attributes_by_id(attribute_id):
    logger.Log('FUNCTION CALL: delete_tenant_attributes_by_id()', logging.DEBUG)
    sql = """DELETE FROM `ops_man_tenant_attribute` WHERE id = %s""" % (attribute_id)
    logger.Log('delete_tenant_attributes_by_id: \n\n%s\n\n' % sql, logging.DEBUG)
    query_database(sql)

def get_ssh_attribute_type_id():
    logger.Log('FUNCTION CALL: get_ssh_attribute_type_id()', logging.DEBUG)
    sql = "SELECT * FROM `ops_man_tenant_attribute_type` WHERE `name` = 'ssh_key'"
    logger.Log('get_ssh_attribute_type_id: \n\n%s\n\n' % sql, logging.DEBUG)
    
    
    ssh_attribute_type = query_database(sql)
    if(len(ssh_attribute_type) > 0):
        return ssh_attribute_type[0]
    return None

def check_if_tenant_attribute_type_already_exists(name):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = "SELECT 1 FROM `ops_man_tenant_attribute_type` WHERE `name` = '%s'" % (name)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    tenant_attribute_exists = query_database(sql)

    return tenant_attribute_exists

def check_if_user_attribute_type_already_exists(name):
    logger.Log('FUNCTION CALL: check_if_user_attribute_type_already_exists()', logging.DEBUG)
    sql = "SELECT 1 FROM `ops_man_ldap_user_attribute_type` WHERE `name` = '%s'" % (name)
    logger.Log('check_if_user_attribute_type_already_exists: \n\n%s\n\n' % sql, logging.DEBUG)

    if(len(query_database(sql)) > 0):
        return True
    return False


def check_if_tenant_attribute_type_already_exists_using_id(id):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = "SELECT 1 FROM `ops_man_tenant_attribute_type` WHERE `id` = '%s'" % (id)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    tenant_attribute_exists = query_database(sql)

    return tenant_attribute_exists

def check_if_user_attribute_type_already_exists_using_id(id):
    logger.Log('FUNCTION CALL: check_if_user_attribute_type_already_exists_using_id()', logging.DEBUG)
    sql = "SELECT 1 FROM `ops_man_ldap_user_attribute_type` WHERE `id` = '%s'" % (id)
    logger.Log('check_if_user_attribute_type_already_exists_using_id: \n\n%s\n\n' % sql, logging.DEBUG)

    return len(query_database(sql)) > 0

def get_user_attributes_by_id(id):
    logger.Log('FUNCTION CALL: check_if_user_attribute_type_already_exists_using_id()', logging.DEBUG)
    sql = """select b.`name` as attribute_name, a.`value` as attribute_value, a.`id` as user_attribute_id from ops_man_ldap_user_attribute a
            JOIN ops_man_ldap_user_attribute_type b on a.ops_man_ldap_user_attribute_type_id = b.id
            where a.ops_man_ldap_user_id = %s""" % (id)
    logger.Log('check_if_user_attribute_type_already_exists_using_id: \n\n%s\n\n' % sql, logging.DEBUG)
    
    return query_database(sql)


def check_if_datacenter_already_exists_using_id(id):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = "SELECT 1 FROM `ops_man_datacenter` WHERE `id` = '%s'" % (id)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    datacenter_exists = query_database(sql)

    return datacenter_exists


def check_if_datacenter_already_exists_using_name(name):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = "SELECT 1 FROM `ops_man_datacenter` WHERE `name` = '%s'" % (name)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    datacenter_exists = query_database(sql)

    return datacenter_exists


def check_if_environment_already_exists_using_name(name):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = "SELECT 1 FROM `ops_man_environment` WHERE `name` = '%s'" % (name)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    environment_exists = query_database(sql)

    return environment_exists


def check_if_environment_already_exists_using_id(id):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = "SELECT 1 FROM `ops_man_environment` WHERE `id` = '%s'" % (id)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    environment_exists = query_database(sql)

    return environment_exists


def delete_tenant_attribute_type(id):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = "DELETE FROM `ops_man_tenant_attribute_type` WHERE `id` = '%s'" % (id)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)

def delete_user_attribute_type(id):
    logger.Log('FUNCTION CALL: delete_user_attribute_type()', logging.DEBUG)
    sql = "DELETE FROM `ops_man_ldap_user_attribute_type` WHERE `id` = '%s'" % (id)
    logger.Log('delete_user_attribute_type: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)


def delete_datacenter(id):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = "DELETE FROM `ops_man_datacenter` WHERE `id` = '%s'" % (id)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)

def Update_datacenter_by_id(id, name):
    logger.Log('FUNCTION CALL: Update_datacenter_by_id()', logging.DEBUG)
    sql = "update `ops_man_datacenter` set name = '%s' WHERE `id` = %s" % (name, id)
    logger.Log('Update_datacenter_by_id: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)

def Update_environment_by_id(id, name):
    logger.Log('FUNCTION CALL: Update_environment_by_id()', logging.DEBUG)
    sql = "update `ops_man_environment` set name = '%s' WHERE `id` = %s" % (name, id)
    logger.Log('Update_environment_by_id: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)


def delete_environment(id):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = "DELETE FROM `ops_man_environment` WHERE `id` = '%s'" % (id)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    query_database(sql)


def get_all_tenant_attribute_types_for_form():
    logger.Log('FUNCTION CALL: get_all_tenant_attribute_types_for_form()', logging.DEBUG)
    sql = """SELECT `ops_man_tenant_attribute_type`.`id`, `ops_man_tenant_attribute_type`.`name` FROM `ops_man_tenant_attribute_type` where name <> 'ssh_key'"""
    logger.Log('get_all_tenant_attribute_types_for_form: \n\n%s\n\n' % sql, logging.DEBUG)

    tenant_attribute_types = query_database(sql)
    tenant_attribute_types = [(item['id'], item['name']) for item in tenant_attribute_types]

    return tenant_attribute_types


def get_ssh_tenant_attribute_types_for_form():
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """SELECT `ops_man_tenant_attribute_type`.`id`, `ops_man_tenant_attribute_type`.`name` FROM `ops_man_tenant_attribute_type` where name = 'ssh_key'"""
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    tenant_attribute_types = query_database(sql)
    tenant_attribute_types = [(item['id'], item['name']) for item in tenant_attribute_types]

    return tenant_attribute_types



def get_tenant(name):
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """SELECT * FROM `ops_man_tenant` WHERE `ops_man_tenant`.`name` = '%s'""" % (name)
    logger.Log('tenant_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    data_tenant = query_database(sql)

    return data_tenant


def datacenter_get_all():
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """SELECT `ops_man_datacenter`.`id`, `ops_man_datacenter`.`name` FROM `ops_man_datacenter`"""
    logger.Log('datacenters_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    datacenters = query_database(sql)

    return datacenters


def environment_get_all():
    logger.Log('FUNCTION CALL: tenant_get_all()', logging.DEBUG)
    sql = """SELECT `ops_man_environment`.`id`, `ops_man_environment`.`name` FROM `ops_man_environment`"""
    logger.Log('environments_get_all: \n\n%s\n\n' % sql, logging.DEBUG)

    environments = query_database(sql)

    return environments


def create_history(username,action,target,data_json):
    logger.Log('FUNCTION CALL: create_history()', logging.DEBUG)
    json_string = json.dumps(data_json, default=utility.serialize_datetime)
    sql = """INSERT INTO ops_man_history (username, action, target, data_json)
    VALUES ('%s', '%s', '%s', '%s');""" % (username,action,target,json_string)

    query_database(sql)
    logger.Log('create_history: \n\n%s\n\n' % sql, logging.DEBUG)


def get_history_data():
    logger.Log('FUNCTION CALL: get_history_data()', logging.DEBUG)
    sql = """Select * from ops_man_history"""
    logger.Log('get_history_data: \n\n%s\n\n' % sql, logging.DEBUG)

    return query_database(sql)

def get_history_data_by_id(id):
    logger.Log('FUNCTION CALL: get_history_data_by_id()', logging.DEBUG)
    sql = """Select * from ops_man_history where `id` = %s""" %(id)
    data = query_database(sql)
    logger.Log('get_history_data_by_id: \n\n%s\n\n' % sql, logging.DEBUG)
    if len(data) > 0:
        return data [0]
    return {}



def tenant_get_by_name(tenant):
    logger.Log('FUNCTION CALL: tenant_get_by_name()', logging.DEBUG)
    sql = """SELECT `ops_man_tenant`.`id`,`ops_man_tenant`.`tenant`, `ops_man_tenant`.`last_updated` FROM `ops_man_tenant` WHERE `ops_man_tenant`.`tenant` = '%s'""" % (
        tenant)
    logger.Log('tenant_get_by_name: \n\n%s\n\n' % sql, logging.DEBUG)

    try:
        data_tenant = query_database(sql)[0]
        return data_tenant
    except Exception as e:
        return False
