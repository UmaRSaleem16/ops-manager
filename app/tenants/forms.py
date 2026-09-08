from flask_wtf import Form
from wtforms import StringField, SubmitField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, InputRequired, ValidationError

from app import database

def no_spaces(form, field):
    if ' ' in field.data:
        raise ValidationError('Spaces are not allowed in tenant name.')

def service_last_digits(form, field):
    name = form.name.data
    service_id = field.data

    # Check if service is not empty and name ends with service
    if service_id and not name.endswith(str(service_id)):
        raise ValidationError('Service Id should be the last digits of the Tenant name.')

class TenantForm(Form):
    service_id = IntegerField('Service ID', validators=[InputRequired()])
    name = StringField('Name', default="", validators=[InputRequired(), Length(min=2, max=80), no_spaces])
    submit = SubmitField('Add Tenant')

class TenantAttributeSSHValueForm(Form):
    value = TextAreaField('Value', validators=[InputRequired()], render_kw={"rows": 5})
    tenant_attribute_type = SelectField('Tenant Attribute Type',
                                        choices=database.get_ssh_tenant_attribute_types_for_form(),
                                        validators=[InputRequired()])
    submit = SubmitField('Add SSH Value')

class TenantAttributeValueForm(Form):
    value = TextAreaField('Value', validators=[InputRequired()], render_kw={"rows": 5})
    tenant_attribute_type = SelectField('Tenant Attribute Type',
                                        choices=database.get_all_tenant_attribute_types_for_form(),
                                        validators=[InputRequired()])
    submit = SubmitField('Add Value')

