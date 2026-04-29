from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from arasCore.lib.core.extensions import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(
    subject, sender, recipients, text_body, html_body, attachments=None, sync=False
):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    if sync:
        mail.send(msg)
    else:
        Thread(
            target=send_async_email, args=(current_app._get_current_object(), msg)
        ).start()


# def send_email(to, subject, template, **kwargs):
#     app = current_app._get_current_object()
#     msg = Message(
#         app.config["MAIL_SUBJECT_PREFIX"] + " " + subject,
#         sender=app.config["MAIL_SENDER"],
#         recipients=[to],
#     )
#     msg.body = render_template(template + ".txt", **kwargs)
#     msg.html = render_template(template + ".html", **kwargs)
#     thr = Thread(target=send_async_email, args=[app, msg])
#     thr.start()
#     return thr
