import os
import ssl

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
from werkzeug.contrib.fixers import ProxyFix

bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
load_dotenv()


def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    crt_cert_path = os.path.abspath(os.path.join(script_dir, '..', 'src', os.getenv('CRT_CERTIFICATE', None)))
    key_cert_path = os.path.abspath(os.path.join(script_dir, '..', 'src', os.getenv('KEY_CERTIFICATE', None)))
    log_file = os.path.abspath(os.path.join(script_dir, '..', 'log', os.getenv('LOG_FILE', None)))
    ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ctx.load_cert_chain(crt_cert_path, key_cert_path)

    app.config['MAIL_SERVER'] = os.getenv('EMAIL_HOST', None) #"smtp.googlemail.com"
    app.config['MAIL_PORT'] = os.getenv('EMAIL_PORT', None) #587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER', None)
    app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS', None)
    app.config['EMAIL_SENDER'] = os.getenv('EMAIL_SENDER', None)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY_FLASK', None)     #
    app.config['RECAPTCHA_PUBLIC_KEY'] = os.getenv('RECAPTCHA_PUBLIC_KEY', None)
    app.config['RECAPTCHA_PRIVATE_KEY'] = os.getenv('RECAPTCHA_PRIVATE_KEY', None)
    app.config['MYSQL_DATABASE_USER'] = os.getenv('MYSQL_DATABASE_USER', None)
    app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv('MYSQL_DATABASE_PASSWORD', None)
    app.config['MYSQL_DATABASE_HOST'] = os.getenv('MYSQL_DATABASE_HOST', None)
    app.config['MYSQL_DATABASE_DB'] = os.getenv('MYSQL_DATABASE_DB', None)
    app.config['MYSQL_DATABASE_PORT'] = os.getenv('MYSQL_DATABASE_PORT', None)
    app.config['LOGFILE'] = log_file
    app.config['APP_HOST'] = os.getenv('APP_HOST', None)
    app.config['APP_PORT'] = os.getenv('APP_PORT', None)
    app.config['company'] = os.getenv('COMPANY', None)
    app.config['TESTING'] = os.getenv('DEBUG', None)
    app.config['AUTHENTICATION_TYPE'] = os.getenv('AUTHENTICATION_TYPE', None)
    app.config['PASSWORD_EXPIRY_MINUTES'] = os.getenv('PASSWORD_EXPIRY_MINUTES', None)
    app.config['LDAP_HOST'] = os.getenv('LDAP_HOST', None)
    app.config['LDAP_BIND_NAME'] = os.getenv('LDAP_BIND_NAME', None)
    app.config['LDAP_ADMIN'] = os.getenv('LDAP_ADMIN', None)
    app.config['LDAP_ADMIN_PASS'] = os.getenv('LDAP_ADMIN_PASS', None)

    # domain = os.getenv('DOMAIN', None)                                 # "contoso.com"
    # BASEDN = os.getenv('BASEDN', None)                                 # "OU=Users,dc=contoso,dc=com"
    # user_admin = os.getenv('USER_ADMIN', None)                         # "administrador"
    # passwd_admin = os.getenv('PASSWORD_ADMIN', None)                   # "fsdfsfs#@$SDA"
    # enable = os.getenv('SLACK_ACTIVATION', None)                       #  True  # Slack Activation True to activate

    bcrypt.init_app(app)
    login_manager.init_app(app)
    global mail
    mail = Mail(app)
    from app.users.routes import users
    from app.datacenter.routes import datacenters
    from app.tenants.routes import tenants
    from app.attributes.routes import attributes
    from app.permission_matrix.routes import permission_matrix
    from app.groups.routes import groups
    from app.errors.handlers import errors
    from app.history.routes import history


    app.register_blueprint(users)
    app.register_blueprint(tenants)
    app.register_blueprint(attributes)
    app.register_blueprint(datacenters)
    app.register_blueprint(permission_matrix)
    app.register_blueprint(groups)
    app.register_blueprint(errors)
    app.register_blueprint(history)

    return app


