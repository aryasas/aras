# -*- coding: utf-8 -*-
"""
arasCore/forms.py — built-in auth forms.

Pure ArasGen. No widgets are spelled out: type and widget are inferred
from the field name (``password`` → Password input, ``email`` → email
input, ``remember_me`` → checkbox). Override only when the name lies.
"""
from arasCore import ArasForm, Col, Boolean, String


class LoginForm(ArasForm):
    email_or_username = String(null=False, label="Email or Username")
    password          = Col(null=False)
    remember_me       = Boolean(default=False, label="Remember me")


class RegisterForm(ArasForm):
    username  = String(null=False, length=64)
    email     = Col(null=False)
    password  = Col(null=False, length=128)
    password2 = Col(null=False, length=128, label="Confirm Password")


class ChangePasswordForm(ArasForm):
    old_password  = Col(null=False, label="Current Password")
    new_password  = Col(null=False, length=128)
    new_password2 = Col(null=False, length=128, label="Confirm")


class PasswordResetRequestForm(ArasForm):
    email = Col(null=False)


class PasswordResetForm(ArasForm):
    password         = Col(null=False, length=128, label="New Password")
    confirm_password = Col(null=False, length=128)


class ChangeEmailForm(ArasForm):
    email    = Col(null=False, label="New Email")
    password = Col(null=False, label="Current Password")
