from flask_wtf import Form
from wtforms import SelectField
from wtforms.validators import InputRequired, DataRequired

from app import database

class PermissionMatrixForm(Form):
    security_group = SelectField('Group', default='NULL', choices=[('', '-')] + database.get_all_groups_for_form(), validators=[DataRequired()])
    environment = SelectField('Environment', default='NULL', choices=[('', '-')] + database.get_all_environments_for_form(), validators=[DataRequired()])
    datacenter = SelectField('DataCenter', default='NULL', choices=[('', '-')] + database.get_all_datacenters_for_form(), validators=[DataRequired()])

