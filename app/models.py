from flask_mail import Message
from flask import flash
import os
import ssl
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app import database, mail
import json
from app import logger
import logging
import ssl
import sys
from jsondb import Database
from ldap3 import Tls, NTLM, Connection, Server, SUBTREE, MODIFY_REPLACE
from slackclient import SlackClient

from flask import session, current_app, url_for
from app import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


# ===============

# file = open("src/config.json")
# variables = json.loads(file.read())

# # ===============

# SLACK_BOT_TOKEN = variables['SLACK_BOT_TOKEN']          #
# slack_db = "src/" + variables['slack_db']               # slack db users

# db = Database(slack_db)

# sc = SlackClient(SLACK_BOT_TOKEN)

# ===============


def disconnect():
    """
    Force to disconnect the ldap connection with the server.
    """
    pass


def conx(domain, user, passwd):
    """
    Connection to the server
    """
    tls_configuration = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

    # define the server and the connection
    s = Server(domain, port=636, use_ssl=True, tls=tls_configuration)
    conn = Connection(s, domain + "\\" + user, passwd, authentication=NTLM)
    conn.start_tls()
    conn.bind()

    # perform the Bind operation
    try:
        if not conn.bind():
            conn.unbind()
            raise ValueError("Invalid credentials")
    finally:
        pass

    # print("Connected")

    return conn


# def search_slack_id(email):
#     for users in db['members']:
#         # print(users)
#         if not (users['is_bot'] and users['deleted']):
#             # noinspection PyBroadException
#             try:
#                 if users['profile']['email'] == email:
#                     # print(users['id'], users['profile']['email'])
#                     return users['id']
#             except:
#                 print("User with this email: " + email + " no found!!")


def search_userx(username, conn, basedn):
    """
        Verifies credentials for username and password.
        Returns True on success or False on failure
    """
    global user_dn
    SEARCHFILTER = '(&(|' \
                   '(userPrincipalName=' + username + ')' \
                                                      '(samaccountname=' + username + ')' \
                                                                                      '(mail=' + username + '))' \
                                                                                                            '(objectClass=person))'
    # SEARCHFILTER_DEFAULT = '(objectClass=person)'

    conn.search(search_base=basedn, search_filter=SEARCHFILTER,
                search_scope=SUBTREE, attributes=['cn',
                                                  'mail'], paged_size=5)
    for entry in conn.response:
        # print(entry)
        # user_dn1 = entry.get("dn")
        user_mail = entry.get("attributes")["mail"]
        if entry.get("dn") and entry.get("attributes"):
            if entry.get("attributes").get("cn"):
                user_dn = entry.get("dn")

        return user_dn, user_mail


def authenticate(domain, username, password):
    """
    Verifies credentials for username and password.
    Returns True on success or False on failure
    """

    tls_configuration = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
    # define the server and the connection
    s = Server(domain, port=636, use_ssl=True, tls=tls_configuration)
    conn = Connection(s, domain + "\\" + username, password, authentication=NTLM)
    conn.start_tls()
    conn.bind()
    # print(conn.usage)
    # perform the Bind operation
    try:
        if not conn.bind():
            print("Not Connected")
            conn.unbind()
            return False
        else:
            print("Connected")
            conn.unbind()
            return True
    finally:
        pass


# def reset_passwd(domain, user_admin, passwd_admin, basedn, username, current, new_passwd, enable):
#     """
#     Verifies credentials for username and password.
#     Returns True on success or False on failure
#     """

#     conn = conx(domain, user_admin, passwd_admin)
#     user, email = search_userx(username, conn, basedn)

#     try:
#         if not authenticate(domain, username, current):
#             return False
#         else:
#             # perform the Bind operation

#             enc_pwd = '"{}"'.format(new_passwd).encode('utf-16-le')

#             changes = {'unicodePwd': [(MODIFY_REPLACE, [enc_pwd])]}

#             x = conn.modify(user, changes=changes)

#             print(x)
#             # Slack Notification for the user
#             if enable:
#                 x = search_slack_id(email)

#                 result = sc.api_call("chat.postMessage", channel=x,
#                                      text="You password was reset! testing :) not panic :tada:", as_user=True)

#                 print("Result: ", result['ok'])
#             else:
#                 pass

#         # a new password is set, hashed with sha256 and a random salt
#         return True

#     finally:
#         conn.unbind()


# =================================================

@login_manager.user_loader
def load_user(user_id):
    logger.Log('FUNCTION CALL: load_user()', logging.DEBUG)

    sql = """SELECT `id`, `username`, `password` FROM `ops_man_ldap_user` WHERE `id` = %s""" % (int(user_id))
    logger.Log('load_user: %s' % sql, logging.DEBUG)

    try:
        item = json.dumps(database.query_database(sql)[0])
    except:
        item = None
        pass

    if item:
        return str_to_class(item)
    else:
        return None


class User(object):

    def __init__(self, username):
        logger.Log('FUNCTION CALL: User()', logging.DEBUG)

        sql = """SELECT * FROM `ops_man_ldap_user` WHERE `username` = '%s'""" % (username)
        logger.Log('User: %s' % sql, logging.DEBUG)

        self.user_data = database.query_database(sql)[0]

        self.id = self.user_data['id']
        self.username = self.user_data['username']
        self.password = self.user_data['password']
        self.email = self.user_data['email'].lower()

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id, 'username': self.username}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            # user_id = s.loads(token)['user_id']
            # username = s.loads(token)['username']
            return {'user_id': s.loads(token)['user_id'], 'username': s.loads(token)['username']}
        except:
            return None

        # sql = """SELECT * FROM `ops_man_ldap_user` WHERE `id` = %s""" % (user_id)
        # logger.Log('verify_reset_token: %s' % sql, logging.DEBUG)
        # user = database.query_database(sql)[0]
        # return user


def str_to_class(classname):
    return getattr(sys.modules[__name__], 'User')


def set_session_data(username):
    logger.Log('FUNCTION CALL: set_session_data()', logging.DEBUG)

    sql = """SELECT a.*, IFNULL(b.is_admin , 0) AS is_admin, IFNULL(b.is_admin_tenant , 0) AS is_admin_tenant  FROM `ops_man_ldap_user` a
            LEFT JOIN `ops_man_ldap_group` b on a.ops_man_ldap_group = b.id WHERE `username` = '%s'""" % (username)
    logger.Log('set_session_data: %s' % sql, logging.DEBUG)

    user_data = database.query_database(sql)[0]

    session.permanent = False
    session['id'] = user_data['id']
    session['username'] = user_data['username']
    session['password'] = user_data['password']
    session['title'] = user_data['title']
    session['is_admin'] = user_data['is_admin']
    session['is_admin_tenant'] = user_data['is_admin_tenant']
    

    # and here is where we set the group data if we have it
    try:
        group_data = database.user_get_group_by_username(username)
        logger.Log('group_data: %s' % group_data, logging.DEBUG)

        session['group'] = group_data['name']
        # session['site_admin'] = group_data['site_admin']
    except:
        session['group'] = None
        session['site_admin'] = None

        logger.Log('no group data found for user: %s' % username, logging.DEBUG)


def send_reset_email(username):
    try:
        user_obj = User(username['username'])
        token = user_obj.get_reset_token()
        sender_email = current_app.config['EMAIL_SENDER'].lower()
        receiver_email = user_obj.email.lower()
        msg = Message('Password Reset Request',
                    sender=sender_email,
                    recipients=[receiver_email])
        msg.body = f'''To reset your password, visit the following link:
                    {url_for('users.reset_token', token=token, _external=True)}

                    If you did not make this request then simply ignore this email and no changes will be made.
                    '''
        
        message = MIMEText(msg.body, 'plain')
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "Password Reset Request"
        # message["Bcc"] = receiver_email

        print(msg.body)
        # mail.send(msg)
        send_email_with_ses(sender_email, receiver_email, message.as_string())
    
    except Exception as e:
        flash("Error at sending Reset password email.", "danger")
        logger.Log("Error at sending Reset password email: %s" %e, logging.ERROR)
        raise e


def send_email_with_ses(sender,reciever,message) :
    # getting the credentials fron evironemnt
    host = current_app.config['MAIL_SERVER'] #'email-smtp.us-west-2.amazonaws.com'
    user = current_app.config['MAIL_USERNAME']
    password = current_app.config['MAIL_PASSWORD']
    port = current_app.config['MAIL_PORT']

    # setting up ssl context
    context = ssl.create_default_context()
    # creating an unsecure smtp connection
    with SMTP(host,port) as server :
        # securing using tls
        server.starttls(context=context)
        # authenticating with the server to prove our identity
        server.login(user=user, password=password)
        # sending a plain text email
        server.sendmail(sender, reciever, message)
