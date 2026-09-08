from flask import session
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError

from app import database


class RegistrationForm(Form):
  title = StringField('Title', default="", validators=[DataRequired(), Length(max=80)])
  name = StringField('Name', default="", validators=[DataRequired(), Length(min=2, max=80)])
  email = StringField('Email', validators=[DataRequired(), Length(min=2, max=80)])
  username = StringField('Username', validators=[DataRequired(), Length(min=2, max=80)])
  password = PasswordField('Password', validators=[DataRequired()])
  confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
  submit = SubmitField('Sign Up')


  def validate_username(self, username):
    user = database.user_validate('username', username.data)
    if user:
      raise ValidationError('That username is taken, please choose a different one.')


class LoginForm(Form):
  username = StringField('Username', validators=[DataRequired(), Length(min=2, max=80)])
  password = PasswordField('Password', validators=[DataRequired()])
  submit = SubmitField('Login')

class CreateUserForm(Form):
  title = StringField('Title', default="", validators=[DataRequired(), Length(max=80)])
  name = StringField('Name', default="", validators=[DataRequired(), Length(min=2, max=80)])
  email = StringField('Email', validators=[DataRequired(), Length(min=2, max=80)])
  username = StringField('Username', validators=[DataRequired(), Length(min=2, max=80)])
  linux_user_id = StringField('Linux User ID')
  department = StringField('Department')
  security_group = SelectField('Security Group', default='NULL', choices=[('', '-')] + database.get_all_groups_for_form())
  submit = SubmitField('Create User')

class UpdateAccountForm(Form):
  username = StringField('Username', validators=[DataRequired(), Length(min=2, max=80)])
  submit = SubmitField('Update')

  def validate_username(self, username):
    if username.data != session['username']:
      user = database.user_validate('username', username.data)
      if user:
        raise ValidationError('That username is taken, please choose a different one.')

class AddUserAttributeForm(Form):
  user_attributes = SelectField('User Attribute', validators=[DataRequired()])
  attribute_value = TextAreaField('Attribute Value', validators=[DataRequired()], render_kw={"rows": 5})

