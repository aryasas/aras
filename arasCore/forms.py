# -*- coding: utf-8 -*-
"""arasCore/forms.py — Auth forms. Field names match existing templates."""
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from arasCore.lib.ui.forms import ArasForm

class LoginForm(ArasForm):
    email_or_username = StringField("Email or Username", validators=[DataRequired()])
    password          = PasswordField("Password", validators=[DataRequired()])
    remember_me       = BooleanField("Remember me")
    submit            = SubmitField("Login")

class RegisterForm(ArasForm):
    username  = StringField("Username", validators=[DataRequired(), Length(3, 64)])
    email     = StringField("Email", validators=[DataRequired(), Email()])
    password  = PasswordField("Password", validators=[DataRequired(), Length(6, 128)])
    password2 = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit    = SubmitField("Register")

class ChangePasswordForm(ArasForm):
    old_password  = PasswordField("Current Password", validators=[DataRequired()])
    new_password  = PasswordField("New Password", validators=[DataRequired(), Length(6, 128)])
    new_password2 = PasswordField("Confirm", validators=[DataRequired(), EqualTo("new_password")])
    submit        = SubmitField("Change Password")

class PasswordResetRequestForm(ArasForm):
    email  = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send Reset Link")

class PasswordResetForm(ArasForm):
    password         = PasswordField("New Password", validators=[DataRequired(), Length(6, 128)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit           = SubmitField("Reset Password")

class ChangeEmailForm(ArasForm):
    email    = StringField("New Email", validators=[DataRequired(), Email()])
    password = PasswordField("Current Password", validators=[DataRequired()])
    submit   = SubmitField("Request Change")
