from flask_wtf import Form
from wtforms import StringField, SubmitField, IntegerField, BooleanField 
from wtforms.validators import InputRequired


# Define a custom boolean field class
class CustomBooleanField(IntegerField):
    def __call__(self, **kwargs):
        # Render the field with custom HTML
        html = f'<div class="btn-group btn-group-toggle" data-toggle="buttons">'
        html += f'<label class="btn btn-default btn-sm">'
        html += f'<input type="radio" name="{self.name}" id="{self.id}" value="1" {"checked" if self.data else ""}> True'
        html += f'</label>'
        html += f'<label class="btn btn-default btn-sm">'
        html += f'<input type="radio" name="{self.name}" id="is_not_admin" value="0" {"checked" if not self.data else ""}> False'
        html += f'</label></div>'
        return html


class GroupForm(Form):
    name = StringField('Name', validators=[InputRequired()])
    linux_group_id = IntegerField('Linux Group ID', validators=[InputRequired()])
    linux_group_name = StringField('Linux Group Name', validators=[InputRequired()])
    is_admin = CustomBooleanField('Is Admin', default=0)
    is_admin_tenant = CustomBooleanField('Is Tenant Admin', default=0)
    submit = SubmitField('Add Group')
