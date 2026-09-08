from flask_wtf import Form
from wtforms import StringField, SubmitField, IntegerField, HiddenField
from wtforms.validators import InputRequired


class TenantAttributeForm(Form):
    attribute_type = HiddenField(default="tenant")
    name = StringField('Name', validators=[InputRequired()])
    limit = IntegerField('Limit', default=1, validators=[InputRequired()])
    submit = SubmitField('Add Tenant Attribute')

class UserAttributeSetupForm(Form):
    attribute_type = HiddenField(default="user")
    name = StringField('Name', validators=[InputRequired()])
    limit = IntegerField('Limit', default=1, validators=[InputRequired()])
    submit = SubmitField('Add User Attribute')
