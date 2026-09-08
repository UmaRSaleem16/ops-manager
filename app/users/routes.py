import ldap
import json
import socket
import logging
import hashlib
import crypt
import math
import passlib.hash

from ldap3 import Server, Connection, MODIFY_REPLACE

from datetime import datetime, timedelta
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import render_template, url_for, flash, redirect, request, session, abort, Blueprint, current_app, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from wtforms.validators import DataRequired

from app import logger
from app import utility
from app import bcrypt
from app import database
from app.forms import passwdchangeform, ForgotPasswordForm, ResetForgotPassword, ResetExpiredPassword
from app.models import User, set_session_data, send_reset_email
from app.users.forms import RegistrationForm, LoginForm, CreateUserForm, AddUserAttributeForm
from app.utility import serialize_datetime, validate_ssh_key
from app.decorators import validate_route_access

import warnings

warnings.simplefilter(action='ignore')

users = Blueprint('users', __name__)


def test_socket(hostname, port):
    """
    """
    logger.Log('FUNCTION CALL: test_socket()', logging.DEBUG)

    try:
        sock = socket.create_connection((hostname, port), timeout=3)
        return True
    except Exception as e:
        logger.Log("%s" % e, logging.ERROR)
        return False

def generate_hash_sha512(data):
    return hashlib.sha512(data.encode('utf-8')).hexdigest()

def db_auth(username, password):
    """
    """
    user = database.user_get_by_username(username)
    if (user and user['username'] == username):
        hashed_password = generate_hash_sha512(password)
        return user['password'] == hashed_password

def ldap_register(username,password):
    try:
        # Connect to LDAP server
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        conn = ldap.initialize(current_app.config['LDAP_HOST'])
        conn.protocol_version = 3
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.simple_bind_s(current_app.config['LDAP_ADMIN'], current_app.config['LDAP_ADMIN_PASS']) #Bind to admin

        # Prepare user entry attributes
        user_attrs = [
            ('objectClass', [b'inetOrgPerson']),
            ('cn', [username.encode('utf-8')]),
            ('sn', [username.encode('utf-8')]),
            ('uid', [username.encode('utf-8')]),
            ('userPassword', [password.encode('utf-8')]),  # Note: You should hash the password before storing it
            # Add any additional attributes as needed
        ]

        # Construct user DN
        user_dn = 'cn={},{}'.format(username, current_app.config['LDAP_BIND_NAME'])
        # Add user entry to LDAP directory
        conn.add_s(user_dn, user_attrs)
        conn.unbind_s()
        return True, None
    except ldap.ALREADY_EXISTS:
        logger.Log("User Exists error: %s" %e, logging.ERROR)
        return False, 'User already exists'
    except Exception as e:
        logger.Log("error at LDAP user creation: %s" %e, logging.ERROR)
        return False, 'An error occurred: {}'.format(str(e))

def ldap_auth(username, password):
    """
    """
    logger.Log('FUNCTION CALL: ldap_auth()', logging.DEBUG)

    # set up the connection
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    conn = ldap.initialize(current_app.config['LDAP_HOST'])
    conn.protocol_version = 3
    conn.set_option(ldap.OPT_REFERRALS, 0)
    # import pdb;pdb.set_trace()
    try:
        # # username_bind = 'MGMT\\' + username
        # dn = "cn={},{}".format(
        #     ldap.dn.escape_dn_chars(username),
        #
        #     current_app.config['LDAP_BIND_NAME']
        # )
        #
        # conn.simple_bind_s(dn, password)
        username_bind = 'MGMT\\' + username
        conn.simple_bind_s(username_bind, password)
        return True

    except Exception as e:
        logger.Log("error: %s" %e, logging.ERROR)
        return False

def update_db_password(userId,newpassword):
    update_login_password(userId,newpassword)
    set_user_attributes(userId, newpassword)

def update_login_password(userId,newpassword):
    hashed_password = generate_hash_sha512(newpassword)
    password_expiry_time = datetime.now() + timedelta(minutes=int(current_app.config['PASSWORD_EXPIRY_MINUTES']))
    database.user_update_password_and_time_by_id(hashed_password, userId, password_expiry_time)
    
def add_update_user_attribute(user_id, attribute_name, attribute_value):
    if database.check_user_attribute_exist_by_name(user_id,attribute_name):
        database.Update_user_attribute_by_name(user_id,attribute_name,attribute_value)
    else:
        database.add_user_attribute_by_name(user_id,attribute_name,attribute_value)

def set_user_attributes(user_id, user_password):
    
    if(database.check_user_attribute_type_exist_by_name('password_linux')):
        hashed_password_linux = get_password_linux(user_password)
        add_update_user_attribute(user_id, 'password_linux', hashed_password_linux)

    if(database.check_user_attribute_type_exist_by_name('password_mysql')):
        hashed_password_mysql = get_password_mysql(user_password)
        add_update_user_attribute(user_id, 'password_mysql', hashed_password_mysql)

    if(database.check_user_attribute_type_exist_by_name('password_svn')):
        hashed_password_svn = get_svn_password(user_password)
        add_update_user_attribute(user_id, 'password_svn', hashed_password_svn)

    return True

def get_password_linux(password):
    return crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))

def get_password_mysql(password):
    return database.get_mysql_password_hash(password)

def get_svn_password(password):
    return passlib.hash.apr_md5_crypt.hash(password)

def ldap_reset(username,newpassword):
    try:
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        conn = ldap.initialize(current_app.config['LDAP_HOST'])
        conn.protocol_version = 3
        conn.set_option(ldap.OPT_REFERRALS, 0)

        conn.simple_bind_s('MGMT\\' + current_app.config['LDAP_ADMIN'], current_app.config['LDAP_ADMIN_PASS']) #Bind to admin
        # user_dn = "cn={},{}".format(ldap.dn.escape_dn_chars(username), current_app.config['LDAP_BIND_NAME'])

        # user_entry = conn.search_s(user_dn, ldap.SCOPE_SUBTREE)
        result = conn.search_s(current_app.config['LDAP_BIND_NAME'], ldap.SCOPE_SUBTREE, f'(sAMAccountName={username})')
        if result:
            user_dn, user_entry = result[0]
            # Modify the user's password attribute
            # mod_attrs = [(ldap.MOD_REPLACE, 'unicodePwd', newpassword.encode("utf-16-le"))]
            mod_attrs = [(ldap.MOD_REPLACE, 'unicodePwd', [str('"{}"'.format(newpassword)).encode('utf-16-le')])]
            conn.modify_s(user_dn, mod_attrs)

            conn.unbind_s()
            return True
        else:
            flash("User not found: {}".format(username))
            conn.unbind_s()
            return False
    except Exception as e:
        logger.Log('Error at LDAP reset: %s' %e, logging.ERROR)
        return False


@users.route("/register", methods=['GET', 'POST'])
def register():
    logger.Log('FUNCTION CALL: register()', logging.DEBUG)

    if current_user.is_authenticated:
        return redirect(url_for('tenants.all_tenants'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # if (current_app.config['AUTHENTICATION_TYPE'] == 'ldap'):
            #     ldap_register(form.username.data,form.password.data)
            hashed_password = generate_hash_sha512(form.password.data)
            password_expiry_time = datetime.now() + timedelta(minutes=int(current_app.config['PASSWORD_EXPIRY_MINUTES']))
            database.user_create(username=form.username.data, title=form.title.data, password=hashed_password, email=form.email.data, name=form.name.data, password_expiry_at=password_expiry_time)
            flash('Account created for %s!' % (form.username.data), 'success')
            return redirect(url_for('users.login'))
        except Exception as e:
            flash("Error occurred while registering user", 'danger')
            logger.Log("Exception at register: %s" %e, logging.ERROR)

    return render_template('register.html', title='Register', form=form)


@users.route("/", methods=['GET', 'POST'])
@users.route("/login", methods=['GET', 'POST'])
def login():
    logger.Log('FUNCTION CALL: login()', logging.DEBUG)

    if current_user.is_authenticated:
        return redirect(url_for('tenants.all_tenants'))

    form = LoginForm()
    is_local_setting = True if current_app.config['AUTHENTICATION_TYPE'] == 'local' else False
    # import pdb;pdb.set_trace()
    if form.validate_on_submit():
        # this auths against the local database
        if (current_app.config['AUTHENTICATION_TYPE'] == 'local'):
            try:
                user = User(form.username.data)
            except:
                flash('No matching user found! Please register', 'danger')
                return redirect(url_for('users.register'))

            
            if user and db_auth(form.username.data, form.password.data):
                user_data = database.user_get_by_username(form.username.data)
                if user_data['password_expiry_at'] and datetime.now() < user_data['password_expiry_at']:
                    login_user(user)
                    set_session_data(form.username.data)
                    # set_user_attributes(session['id'], form.password.data)
                    next_page = request.args.get('next')
                    if(session['is_admin']):
                        return redirect(next_page) if next_page else redirect(url_for('users.all_users'))
                    elif(session['is_admin_tenant']):
                        return redirect(url_for('tenants.all_tenants'))
                    else:
                        return redirect(url_for('users.user_profile'))

                else:
                    reset_form = ResetExpiredPassword()
                    flash('Your password is expired, please reset', 'danger')
                    return render_template('reset-expired-pass.html', title='Reset Password', form=reset_form, 
                    username=user_data['username'], 
                    current_password=form.password.data, 
                    user_id = user_data['id'])
            else:
                flash('Local auth unsuccessful. Please check username and password', 'danger')

        # ldap authentication
        elif (current_app.config['AUTHENTICATION_TYPE'] == 'ldap'):
            logger.Log("Attempting LDAP auth...", logging.DEBUG)

            if test_socket(current_app.config['LDAP_HOST'].split("/")[2].split(":")[0],
                           current_app.config['LDAP_HOST'].split("/")[2].split(":")[1]):
                if ldap_auth(form.username.data, form.password.data):
                    # flash('LDAP successful!', 'success')
                    # if we already have an account we load our stuff and update...
                    flash("LDAP Authentication Successful.", "success")
                    try:
                        user = User(form.username.data)
                        login_user(user)
                        set_session_data(form.username.data)
                        next_page = request.args.get('next')

                        # we need to update the password too
                        hashed_password = generate_hash_sha512(form.password.data)
                        database.user_update_password_by_id(hashed_password, session['id'])
                        # set_user_attributes(session['id'], form.password.data)
                    # otherwise we have to insert and load
                    except Exception as e:
                        logger.Log('Error at LDAP login: %s' % e, logging.ERROR)
                        hashed_password = generate_hash_sha512(form.password.data)
                        password_expiry_time = datetime.now() + timedelta(minutes=int(current_app.config['PASSWORD_EXPIRY_MINUTES']))
                        database.user_create_partial(username=form.username.data, password=hashed_password, password_expiry_at=password_expiry_time)
                        user = User(form.username.data)
                        login_user(user)
                        set_session_data(form.username.data)
                        next_page = request.args.get('next')

                    # push em to the redirect
                    if(session['is_admin'] or session['is_admin_tenant']):
                        return redirect(next_page) if next_page else redirect(url_for('tenants.all_tenants'))
                    else:
                        return redirect(url_for('users.user_profile'))
                else:
                    flash('LDAP auth unsuccessful. Please check username and password', 'danger')
            else:
                logger.Log("LDAP target unavailable", logging.ERROR)
                flash('LDAP target unavailable. Please contact administrator', 'danger')

        else:
            flash('No supported AUTHENTICATION_TYPE is set.', 'danger')
    
    if form.errors:
        flash('Username & Password is missing.', 'danger')
    
    return render_template('login.html', title='Login', form=form, is_local_setting=is_local_setting)


@users.route("/logout")
def logout():
    logger.Log('FUNCTION CALL: logout()', logging.DEBUG)
    logout_user()
    session.clear()
    session.pop('id', None)
    session.pop('username', None)
    session.pop('password', None)
    session.pop('group', None)
    session.pop('site_admin', None)
    return redirect(url_for('users.login'))


# Comment - change in this file
# I have the removed the account method that was here as we use the user page for account in layout.html
# End of comment


def get_user_list():
    logger.Log('FUNCTION CALL: get_user_list()', logging.DEBUG)
    users = database.user_get_all()
    return users

@users.route("/create-user", methods=['POST'])
@login_required
@validate_route_access
def create_user():
    form = CreateUserForm()
    form.security_group.choices = database.get_all_groups_for_form()

    return_data = {}

    try:
        form.security_group.data =  int(form.security_group.data)

        if form.validate_on_submit():
            database.user_create_full(form.data)
            flash("User added successfully.", 'success')
        else:
            flash("Invalid Data provided. please provided user details.", 'danger')
    except Exception as e:
        logger.Log('Error while creating user: %s' %e, logging.ERROR)
        flash("Something went wrong, please try again", 'danger')

    return redirect(url_for('users.all_users'))

@users.route("/edit-user", methods=['POST'])
@login_required
@validate_route_access
def edit_user():
    logger.Log("FUNCTION CALL: edit_user()", logging.DEBUG)
    # if not session['site_admin']:
    #     if (int(session['id']) != int(id)):
    #         abort(403)

    data = dict(request.json)
    try:
        
        security_group = data.get('group_id') if data.get('group_id') else 'NULL'
        linux_user_id = data.get('linux_user_id') if(data.get('linux_user_id').strip()) else 'NULL'
        department = data.get('department') if(data.get('department').strip() or data.get('department') is not None) else 'NULL'
        database.user_edit_by_id(data.get('user_id'), linux_user_id, department, security_group)

        flash("user %s edited successfully" % data.get('name'), 'success')
        return json.dumps({'success': True}), 200

    except Exception as e:
        logger.Log('Error while editing user: %s' %e, logging.ERROR)
        flash("Error editing user %s." % data.get('name'), 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500


@users.route("/edit-user-attribute", methods=['POST'])
@login_required
@validate_route_access
def edit_user_attribute():
    logger.Log("FUNCTION CALL: edit_user_attribute()", logging.DEBUG)
    # if not session['site_admin']:
    #     if (int(session['id']) != int(id)):
    #         abort(403)

    data = dict(request.json)
    try:
        user_attribute_value = data.get('attribute_value') if(data.get('attribute_value')) else 'NULL'
        user_attribute_detail = database.get_user_attribute_by_id(data.get('user_attribute_id'))

        is_valid = True
        if(user_attribute_detail and user_attribute_detail.get('attribute_name') == 'ssh_key'):
            is_valid, msg = validate_ssh_key(ssh_key=user_attribute_value)
        
        if not is_valid:
            return json.dumps({'success': False, 'error': msg}), 400
        
        database.Update_user_attribute_by_id(data.get('user_attribute_id'), user_attribute_value)
        flash("user Attribute edited successfully", 'success')
        return json.dumps({'success': True}), 200
        
    except Exception as e:
        logger.Log('Error while editing user attribute: %s' %e, logging.ERROR)
        # flash("Error editing user attribute.", 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500

@users.route("/delete-user-attribute/<id>", methods=['DELETE'])
@login_required
@validate_route_access
def delete_user_attribute(id):
    logger.Log("FUNCTION CALL: delete_user_attribute()", logging.DEBUG)
    # if not session['site_admin']:
    #     if (int(session['id']) != int(id)):
    #         abort(403)

    try:
        # department = data.get('department') if(data.get('department').strip() or data.get('department') is not None) else 'NULL'
        database.delete_user_attribute_by_id(id)

        flash("user Attribute deleted successfully!", 'success')
        return json.dumps({'success': True}), 200

    except Exception as e:
        logger.Log('Error while deleting attribute: %s' %e, logging.ERROR)
        flash("Error deleting attribute.", 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500



@users.route("/get-users")
@login_required
@validate_route_access
def get_ajax_users():
    logger.Log('FUNCTION CALL: get_ajax_users()', logging.DEBUG)

    try:
        users = database.user_get_all_with_group()
        group = request.args.get('group')
        if group:
            users = database.user_get_all_with_group_by_group_id(group)


        draw = int(request.args.get('draw', 0))
        start = int(request.args.get('start', 0))
        length = int(request.args.get('length', 10))
        search_value = request.args.get('search[value]', '')
        order_column_index = int(request.args.get('order[0][column]', 0))
        order_direction = request.args.get('order[0][dir]', 'asc')  

        filtered_data = [record for record in users if search_value.lower() in str(record).lower()]
        sorted_data = sorted(filtered_data, key=lambda x: x.get('id'), reverse=(order_direction == 'desc'))
        # Apply pagination
        paginated_data = sorted_data[start:start + length]

        # Prepare response
        response = {
            "draw": draw,
            "recordsTotal": len(users),
            "recordsFiltered": len(filtered_data),
            "data": paginated_data
        }
    except Exception as e:
        logger.Log('Error while getting users: %s' %e, logging.ERROR)
        return jsonify({'success': False, 'error': repr(e)}), 500

    return jsonify(response)




@users.route("/users", methods=['GET', 'POST'])
@login_required
@validate_route_access
def all_users():
    logger.Log("FUNCTION CALL: all_users()", logging.DEBUG)

    form = CreateUserForm()
    form.security_group.choices = database.get_all_groups_for_form()

    # if not session['site_admin']:
    #     abort(403)

    if request.method == "POST":
        data = {}
        submitter = request.form.get('submitter')
        return_data = {}
        

        if (submitter == 'user_delete'):
            data['username'] = request.form.get('username')
            data['user_id'] = request.form.get('id')
            logger.Log("input_data: %s" % data, logging.DEBUG)
            logger.Log("%s | user delete command called" % session['username'], logging.INFO)

            return_data['input_data'] = data

            # lets go nuke this user
            database.user_delete_by_id(data['user_id'])
            # lets see if we were successful
            try:
                user = database.user_get_by_id(data['user_id'])
                return_data['errors'] = 'User deletion unsuccessful!'
                logger.Log("%s | user deletion unsuccessful, user_id: %s" % (session['username'], data['user_id']),
                           logging.ERROR)
                return json.dumps(return_data)
            except:
                logger.Log("%s | user delete command successful" % session['username'], logging.INFO)
                database.history_admin_insert_command(session['username'], 'user_delete', json.dumps(data))
                return json.dumps(return_data)

        if (submitter == 'user_edit'):
            data['user_id'] = request.form.get('user_id')
            data['group_id'] = request.form.get('group_id')
            logger.Log("input_data: %s" % data, logging.DEBUG)
            return_data['input_data'] = data
            logger.Log("%s | user edit command called" % session['username'], logging.INFO)

            try:
                user = database.user_to_group_mapping(data['user_id'])
                if user:
                    database.user_group_update(data['user_id'], data['group_id'])
                    user = database.user_group_validate(data['user_id'], data['group_id'])
            except:
                database.user_group_insert(data['user_id'], data['group_id'])
                user = database.user_group_validate(data['user_id'], data['group_id'])

            if not user:
                return_data['errors'] = 'Unable to map user -> group!'
                logger.Log("%s | user edit command unsuccessful, user_id: %s, group_id: %s" % (
                session['username'], data['user_id'], data['group_id']), logging.ERROR)
            else:
                logger.Log("%s | user edit command successful" % session['username'], logging.INFO)
                database.history_admin_insert_command(session['username'], 'user_edit', json.dumps(data))

            return json.dumps(return_data)
    
    # group = request.args.get('group')
    # if group:
    #     users = database.users_get_by_group_id(group)
    # else:
    #     users = get_user_list()

    # for user in users:
    #     if user['password_expiry_at'] is not None:
    #         user['password_expiry_at'] = user['password_expiry_at'].strftime("%Y-%m-%d %H:%M:%S")
    

    # groups = database.group_get_all()

    # for user in users:
    #     for key, value in user.items():
    #         if value is None:
    #             user[key] = ''
    
    # for user in users:
    #     for group in groups:
    #         if user['ops_man_ldap_group'] == group['id']:
    #             user['group'] = group
    #             break
    #         else:
    #             # If no matching group is found, set group to an empty object
    #             user['group'] = {}

    # dict2 = {group['id']: group for group in groups}

    # user_groups = [{
    #     'id': user['id'], 
    #     'title': user['title'], 
    #     'name': user['name'],
    #     'username': user['username'],
    #     'email': user ['email'],
    #     'linux_user_id': user ['linux_user_id'],
    #     'department': user ['department'],
    #     'group': user['group'],
    #     # 'user_group_name': dict2.get(user['ops_man_ldap_group'], {}).get('name'),
    #     # 'user_group_id': dict2.get(user['ops_man_ldap_group'], {}).get('id')} for user in users
    #     ]

    search_type, search_filter = utility.search_filter()
    
    return render_template('users.html',
                           title='Users',
                           form=form,
                        #    users=users,
                        #    groups=groups,
                        #    user_groups=users,
                           search_type=search_type,
                           search_filter=search_filter
                           )

@users.route("/user-json/<id>", methods=['GET'])
@login_required
@validate_route_access
def user_details_for_json(id):
    logger.Log('FUNCTION CALL: user_details_for_json()', logging.DEBUG)
    try:
        user_data = database.user_get_by_id(id)
        if(user_data):
            if(user_data['ops_man_ldap_group']):
                user_group = database.group_get_by_id(user_data['ops_man_ldap_group'])
                user_data['group'] = user_group
            else: 
                user_data['group'] = {}

            user_attributes = database.get_user_attributes_by_user_id(id)
            if(len(user_attributes)>0):
                user_data['attributes'] = [user_attributes]
            else: 
                user_data['attributes'] = []

        return json.dumps({'success': True, 'data': user_data}, default=serialize_datetime), 200
    except Exception as e:
        logger.Log('Exception at user_details_for_json: %s' %e, logging.ERROR)
        return json.dumps({'success': False, 'error': repr(e)}), 500




# @users.route("/user-credentials")
# @login_required
# def login_user_credentials_attribute():
#     logger.Log('FUNCTION CALL: login_user_credentials_attribute()', logging.DEBUG)

#     form = AddUserAttributeForm()
#     form.user_attributes.choices = database.get_user_system_attribute_for_select()
#     if not session:
#         return redirect(url_for('users.login'))

#     if session and session['id']:
#         #get attributes from database by id
#         user_attributes = database.get_user_system_attributes_by_id(session['id'])
        
#     return render_template('login_user_settings.html',title='User Credentials',user_attributes=user_attributes, form=form)

# @users.route("/user-attributes")
# @login_required
# def login_user_attribute():
#     logger.Log('FUNCTION CALL: login_user_attribute()', logging.DEBUG)

#     form = AddUserAttributeForm()
#     form.user_attributes.choices = database.get_user_other_attribute_for_select()
#     if not session:
#         return redirect(url_for('users.login'))

#     if session and session['id']:
#         #get attributes from database by id
#         user_attributes = database.get_user_other_attributes_by_id(session['id'])
        
#     return render_template('login_user_attributes.html',title='User Attributes',user_attributes=user_attributes, form=form)

def is_user_attribute_limit_reached(tenant_id, attribute_id):
    logger.Log('FUNCTION CALL: is_user_attribute_limit_reached()', logging.DEBUG)
    attribute_count = database.get_user_attribute_count(tenant_id,attribute_id)
    user_attributes_type = database.get_user_attribute_type_by_id(attribute_id)

    # print("limit ====>>> ", limit)
    # print("tenant_attribute ===>>> ", tenant_attribute)
    if user_attributes_type:
        if attribute_count['user_attribute_count'] >= user_attributes_type['limit']:
            return True
    return False


@users.route("/add-user-attribute/<username>", methods=['POST'])
@login_required
@validate_route_access
def add_user_attribute_by_username(username):
    logger.Log('FUNCTION CALL: add_user_attribute_by_username()', logging.DEBUG)
    data = dict(request.json)

    user_id = data.get('user_id')
    user_attributes_id =  int(data.get('user_attributes'))
    try:
        if is_user_attribute_limit_reached(user_id, user_attributes_id):
            flash('Limit reached for this attribute, you can not add more attribute of this type.', 'danger')
            return json.dumps({'success': False, 'error': 'Limit reached for this attribute, you can not add more attribute of this type.'}), 400
        
        user_attribute_detail = database.get_user_attribute_type_by_id(user_attributes_id)

        is_valid = True
        if(user_attribute_detail and user_attribute_detail.get('name') == 'ssh_key'):
            is_valid, msg = validate_ssh_key(ssh_key=data.get('attribute_value'))
        
        if not is_valid:
            return json.dumps({'success': False, 'error': msg}), 400

        database.add_user_attribute(user_id, user_attributes_id, data.get('attribute_value'))
        flash("user Attribute Added successfully.", 'success')
        return json.dumps({'success': True}), 200
    except Exception as e:
        logger.Log('Exception at add_user_attribute(): %s' %e, logging.ERROR)
        flash("Some error occurred while adding attribute.", 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500



@users.route("/add-user-attribute", methods=['POST'])
@login_required
@validate_route_access
def add_user_attribute():
    logger.Log('FUNCTION CALL: add_user_attribute()', logging.DEBUG)

    # form = AddUserAttributeForm()
    username = request.form.get('username')
    user_id = request.form.get('user_id')
    user_attributes_id =  int(request.form.get('user_attributes'))
    try:
        if is_user_attribute_limit_reached(user_id, user_attributes_id):
            flash('Limit reached for this attribute, you can not add more attribute of this type.', 'danger')
            return redirect(url_for('users.user',username=username))

        user_attribute_detail = database.get_user_attribute_type_by_id(user_attributes_id)

        is_valid = True
        if(user_attribute_detail and user_attribute_detail.get('name') == 'ssh_key'):
            is_valid, msg = validate_ssh_key(ssh_key=request.form.get('attribute_value'))
        
        if not is_valid:
            return json.dumps({'success': False, 'error': msg}), 400

        database.add_user_attribute(user_id, user_attributes_id, request.form.get('attribute_value'))
        flash("user Attribute Added successfully.", 'success')
    except Exception as e:
        logger.Log('Exception at add_user_attribute(): %s' %e, logging.ERROR)
        flash("Some error occurred while adding attribute.", 'danger')

    return redirect(url_for('users.user',username=username))

@users.route("/delete_user_attribute_type/<id>", methods=['DELETE'])
@login_required
@validate_route_access
def delete_user_attribute_type(id):
    logger.Log('FUNCTION CALL: delete_user_attribute_type()', logging.DEBUG)

    try:
        database.user_attributes_type_delete(id)
        return json.dumps({'success': True}), 200
    except Exception as e:
        logger.Log('Error at delete_user_attribute_type: %s' %e, logging.ERROR)
        return json.dumps({'success': False, 'error': repr(e)}), 500

@users.route("/user/<id>", methods=['DELETE'])
@login_required
@validate_route_access
def delete_user(id):
    logger.Log('FUNCTION CALL: delete_user()', logging.DEBUG)

    try:
        database.user_delete_by_id(id)
        return json.dumps({'success': True}), 200
    except Exception as e:
        logger.Log('Error at delete_user: %s' %e, logging.ERROR)
        return json.dumps({'success': False, 'error': repr(e)}), 500

@users.route("/user/<username>")
@login_required
@validate_route_access
def user(username):
    logger.Log('FUNCTION CALL: user()', logging.DEBUG)

    user_details = database.user_get_by_username(username)
    if (user_details['ops_man_ldap_group']):
        user_group = database.group_get_by_id(user_details['ops_man_ldap_group'])
    else:
        user_group = {}
    user_attributes = database.get_user_attributes_by_user_id(user_details['id'])
    custom_password_form = AddUserAttributeForm()
    ssh_key_form = AddUserAttributeForm()
    other_attribute_form = AddUserAttributeForm()

    user_attribute_choices = database.get_user_attribute_for_select()

    custom_password_form.user_attributes.choices = list(filter(lambda attribute: attribute[1] in ('password_mysql', 'password_svn', 'password_linux'), user_attribute_choices))
    ssh_key_form.user_attributes.choices = list(filter(lambda attribute: attribute[1] in ('ssh_key'), user_attribute_choices))
    other_attribute_form.user_attributes.choices = list(filter(lambda attribute: attribute[1] not in ('password_mysql', 'password_svn', 'password_linux', 'ssh_key'), user_attribute_choices))

    groups = database.group_get_all()
    search_type, search_filter = utility.search_filter()

    return render_template('user.html',
                           title='User Details',
                           user=user_details,
                           group=user_group,
                           groups=groups,
                           system_attributes=list(filter(lambda attribute: attribute["system_ind"] == True, user_attributes)),
                           ssh_attribute=list(filter(lambda attribute: attribute["attribute_name"] in ('ssh_key'), user_attributes)),
                           other_attributes=list(filter(lambda attribute: (attribute["system_ind"] == False and attribute["attribute_name"] not in ('ssh_key')), user_attributes)),
                           custom_password_form=custom_password_form,
                           ssh_key_form=ssh_key_form,
                           other_attribute_form=other_attribute_form,
                           search_type=search_type,
                          search_filter=search_filter
                           )


@users.route("/user-profile")
@login_required
@validate_route_access
def user_profile():
    logger.Log('FUNCTION CALL: user_profile()', logging.DEBUG)

    if(session['username']):
        username = session['username']
    else:
        return redirect(url_for('users.login'))
        
    user_details = database.user_get_by_username(username)
    if (user_details['ops_man_ldap_group']):
        user_group = database.group_get_by_id(user_details['ops_man_ldap_group'])
    else:
        user_group = {}
    
    user_attributes = database.get_user_attributes_by_user_id(user_details['id'])

    all_user_attribute_types = database.user_attributes_types_get_all()
    user_ssh_attribute_type_exists = any(obj.get('name') == 'ssh_key' for obj in all_user_attribute_types)
    
    reset_password_form = passwdchangeform()
    ssh_key_form = AddUserAttributeForm()
    other_attribute_form = AddUserAttributeForm()

    user_attribute_choices = database.get_user_attribute_for_select()
    
        
    ssh_key_form.user_attributes.choices = list(filter(lambda attribute: attribute[1] in ('ssh_key'), user_attribute_choices))
    other_attribute_form.user_attributes.choices = list(filter(lambda attribute: attribute[1] not in ('password_mysql', 'password_svn', 'password_linux', 'ssh_key'), user_attribute_choices))

    search_type, search_filter = utility.search_filter()
    # import pdb; pdb.set_trace()
    # if reset_password_form.validate_on_submit():
    #     reset_current_password(reset_password_form.current_password.data, reset_password_form.new_password.data)
    #     return redirect(url_for('users.user_profile'))

    return render_template('user_profile.html',
                           title='User Profile',
                           user=user_details,
                           group=user_group,
                           username=username,
                           user_ssh_attribute_type_exists=user_ssh_attribute_type_exists,
                           password_attribute_types=list(filter(lambda attribute: attribute['name'] in ('password_mysql', 'password_svn', 'password_linux'), all_user_attribute_types)),
                           system_attributes=list(filter(lambda attribute: attribute["system_ind"] == True, user_attributes)),
                           ssh_attributes=list(filter(lambda attribute: attribute["attribute_name"] == "ssh_key", user_attributes)),
                           other_attributes=list(filter(lambda attribute: (attribute["system_ind"] == False and attribute["attribute_name"] != "ssh_key"), user_attributes)),
                           ssh_key_form=ssh_key_form,
                           other_attribute_form=other_attribute_form,
                           reset_password_form=reset_password_form,
                           search_type=search_type,
                          search_filter=search_filter
                           )


@users.route("/reset-expired", methods=['POST'])
def reset_expired_password():
    logger.Log('FUNCTION CALL: reset_expired_password()', logging.DEBUG)

    reset_form = ResetExpiredPassword()
    # data = request.form
    try:
        if (current_app.config['AUTHENTICATION_TYPE'] == 'local'):
            try:
                if db_auth(request.form.get('username'), request.form.get('password')):
                    update_db_password(request.form.get('id'), request.form.get('new_password'))
                    flash("Password reset successful. Please login again with new password.", "success")
                    return redirect(url_for('users.login'))
                else:
                    flash("Invalid attempt to change password.","danger")
            except Exception as e:
                flash("Error at Password reset.", 'danger')
                logger.Log("Error at Password reset: %s" %e, logging.ERROR)
        else: #ldap
            try:
                if ldap_auth(request.form.get('username'), request.form.get('password')):
                    is_ldap_success = ldap_reset(request.form.get('username'),request.form.get('new_password'))
                    if(is_ldap_success):
                        update_db_password(request.form.get('id'), request.form.get('new_password'))
                        flash("Password reset successful. Please login again with new password.", "success")
                        return redirect(url_for('users.login'))
                    else:
                        flash("Some error occurred white resetting password.", "danger")
                        return redirect(url_for('users.reset_expired_password'))

                else:
                    flash("Invalid attempt to change password.","danger")
            except Exception as e:
                flash("Error at Password reset.", 'danger')
                logger.Log("Error at Password reset: %s" %e, logging.ERROR)

    except Exception as e:
        logger.Log('Error at rest password: %s' %e, logging.ERROR)
    return render_template('reset-expired-pass.html', title='Reset Password', form=reset_form, 
                    username=request.form.get('username'), 
                    current_password=request.form.get('password'), 
                    user_id = request.form.get('id'))


def reset_current_password(current_password, new_password, login_password_only=False):
    if session and session['username']:
        if (current_app.config['AUTHENTICATION_TYPE'] == 'local'):
            try:
                if db_auth(session['username'], current_password):
                    if login_password_only:
                        update_login_password(session['id'],new_password)
                        message = "Password reset successful!"
                    else:
                        update_db_password(session['id'], new_password)
                        message = "All Password reset successfully."
                    flash(message, "success")
                    return True, message
                else:
                    message = "Current password is not valid."
                    flash(message,"danger")
                    return False, message
            except Exception as e:
                message = "Some error occurred while resetting password."
                flash(message,"danger")
                logger.Log("Error at Password reset: %s" %e, logging.ERROR)
                return False, message
        else: #ldap
            try:
                if ldap_auth(session['username'], current_password):
                    is_ldap_success = ldap_reset(session['username'],new_password)
                    if(is_ldap_success):
                        if login_password_only:
                            update_login_password(session['id'],new_password)
                            message = "LDAP Password reset successful!"
                        else:
                            update_db_password(session['id'],new_password)
                            message = "ldap Password reset successfully."
                        flash(message, "success")
                        return True, message
                    else:
                        message = "Some error occurred white resetting password."
                        flash(message, "danger")
                        return False, message
                else:
                    message = "Current password is not valid."
                    flash(message,"danger")
                    return False, message
            except Exception as e:
                message = "Error at Password reset"
                flash(message, 'danger')
                logger.Log("Error at Password reset: %s" %e, logging.ERROR)
                return False, message 
    else:
        message = "User session not active."
        flash(message, "success")
        return False, message


@users.route("/reset-password-attributes/<username>", methods=['POST'])
@login_required
@validate_route_access
def reset_password_attributes(username):
    logger.Log('FUNCTION CALL: reset_password_attributes()', logging.DEBUG)
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    password_type = request.form.get('password_type')


    if password_type == 'ldap_only':
        reset_current_password(current_password, new_password, login_password_only=True)
        return redirect(url_for('users.user_profile'))

    if (not database.check_user_attribute_type_exist_by_name(password_type)):
        flash("Password Type "+ password_type +" does not exist in the system." , "danger")
        return redirect(url_for('users.user_profile'))

    if db_auth(session['username'], current_password):
        user_details = database.user_get_by_username(username=username)
        if password_type == 'password_svn':
            hashed_password_svn = get_svn_password(new_password)
            add_update_user_attribute(user_details['id'], 'password_svn', hashed_password_svn)
            flash(f"{password_type} updated successfully!", "success")
            return redirect(url_for('users.user_profile'))
        
        elif password_type == 'password_linux':
            hashed_password_linux = get_password_linux(new_password)
            add_update_user_attribute(user_details['id'], 'password_linux', hashed_password_linux)
            flash(f"{password_type} updated successfully!", "success")
            return redirect(url_for('users.user_profile'))
        
        elif password_type == 'password_mysql':
            hashed_password_mysql = get_password_mysql(new_password)
            add_update_user_attribute(user_details['id'], 'password_mysql', hashed_password_mysql)
            flash(f"{password_type} updated successfully!", "success")
            return redirect(url_for('users.user_profile'))
        else:
            flash("Invalid password Type provided.", "danger")
            return redirect(url_for('users.user_profile'))

    else:
        flash("invalid current password provided", "danger")
        return redirect(url_for('users.user_profile'))


@users.route("/reset-current-pass", methods=['POST'])
def reset_current_pass():
    logger.Log('FUNCTION CALL: reset_current_pass()', logging.DEBUG)
    data = dict(request.json)

    if(len(data.get('new_password'))< 8):
        message = "password should be minimum of 8 characters long"
        return json.dumps({'success': False, 'error': message}), 400

    if(data.get('new_password') != data.get('confirm_password')):
        message = "new and confirm password did not match"
        # flash(message, "danger")
        return json.dumps({'success': False, 'error': message}), 400

    is_reset_success, message = reset_current_password(data.get('current_password'), data.get('new_password'))
    if is_reset_success:
        return json.dumps({'success': True}), 200
    else:
        return json.dumps({'success': False, 'error': message}), 500


# @users.route("/", methods=['GET', 'POST'])
@users.route("/reset", methods=['GET', 'POST'])
def reset():
    # context = {}
    form = passwdchangeform()

    if not current_user.is_authenticated:
        return redirect(url_for('users.forgot'))
    
    if form.validate_on_submit():
        reset_current_password(form.current_password.data, form.new_password.data)
        # noinspection PyBroadException
        # try:
        #     if reset_passwd(domain, user_admin, passwd_admin, BASEDN, str(form.username.data), str(form.password.data),
        #                     str(form.new_password.data), enable=enable):
        #         flash(u'Your password was changed for: ' + str(form.username.data), 'success')
        #         return redirect(url_for('reset'))
        #     else:
        #         flash(u'Not possible reset the password for: ' + str(form.username.data), 'success')
        #         return redirect("reset")
        # except ValueError:
        #     pass
    search_type, search_filter = utility.search_filter()
    return render_template('reset.html', title='AD Password Reset',
                           form=form, company=current_app.config['company'],
                           search_type=search_type, search_filter=search_filter)


@users.route("/reset_token/<token>", methods=['GET', 'POST'])
def reset_token(token):
    form = ResetForgotPassword()
    if current_user.is_authenticated:
        return redirect(url_for('tenants.all_tenants'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token.', 'warning')
        return redirect(url_for('users.forgot'))

    if form.validate_on_submit():

        if (current_app.config['AUTHENTICATION_TYPE'] == 'local'):
            update_db_password(user['user_id'],form.new_password.data)
            flash(f"Password has been updated! You are now able to log in.", 'success')
            return redirect(url_for('users.login'))
        else:
            try:
                is_ldap_success = ldap_reset(user['username'],form.new_password.data)
                if(is_ldap_success):
                    update_db_password(user['user_id'],form.new_password.data)
                    flash(f"Password has been updated! You are now able to log in.", 'success')
                    return redirect(url_for('users.login'))
                else:
                    flash("Some error occurred white resetting password.", "danger")
                    return redirect(url_for('users.reset_token', token=token))
            except Exception as e:
                flash("Error at Password reset.", "danger")
                logger.Log("Error at Password reset: %s" %e, logging.ERROR)

    return render_template('reset_forgot_password.html', title='Reset Password', form=form, isTokenized=True)


@users.route("/forgot", methods=['GET', 'POST'])
def forgot():
    if current_user.is_authenticated:
        return redirect(url_for('tenants.all_tenants'))
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = database.user_by_email(form.email.data)    
        if user:
            try:
                send_reset_email(user)
                flash('An email has been sent with instructions to reset your password.', 'info')
                return redirect(url_for('users.login'))
            except Exception as e:
                return redirect(url_for('users.forgot'))
            
        else:
            flash('Email not registered.', 'danger')
    return render_template('forgot.html', title='AD Forgot', form=form)


@users.route("/users_all", methods=['GET', 'POST'])
def users_all():
    users = database.user_get_all()
    return render_template('users.html', title='Users')

