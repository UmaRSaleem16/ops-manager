
from flask import Blueprint, render_template

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(404)
def error_404(error):
  return render_template('404.html'), 404


@errors.app_errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

