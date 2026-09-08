from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, EqualTo


class passwdchangeform(FlaskForm):
    password_type = HiddenField(default="all")
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=8),
                                                                     EqualTo('new_password')])
    submit = SubmitField('Change Password')

class ResetForgotPassword(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()
                                                                    ,Length(min=8)
                                                                    ,EqualTo('new_password')])
    submit = SubmitField('Update Password')
    
class ResetExpiredPassword(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()
                                                                    ,Length(min=8)
                                                                    ,EqualTo('new_password')])
    submit = SubmitField('Update Password')

class ForgotPasswordForm(FlaskForm):
    # username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField('Send Reset Password')


class loginform(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Check')
