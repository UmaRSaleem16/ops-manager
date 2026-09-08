from flask_wtf import Form
from wtforms import StringField, SubmitField, BooleanField, IntegerField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired, Length


class DataCentersForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    type = HiddenField(default="dc")
    submit = SubmitField('Add Datacenter')


class EnvironmentsForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    type = HiddenField(default="env")
    submit = SubmitField('Add Environment')
