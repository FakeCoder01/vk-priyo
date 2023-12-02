from celery import shared_task
from django.core.mail import EmailMessage
from core.models import Profile
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def send_otp_via_email(self, email_type:str, profile_id:str, otp:str=""):
    try:
        email_subject = ""
        email_body = ""

        if email_type == "OTP_RESEND":
            email_subject = "New Code for Priyo"
            email_body = "Dear user,<br>\
                <br>\
                Your One Time Code for Priyo:<br>\
                <strong>" + otp + "</strong><br><br>\
                This code will be valid only for next 15 minutes. \
                If this was not you please ignore this email.<br>\
                you can always contact us at <a href='mailto:support@priyo.ru'>support@priyo.ru</a><br>\
                <br>\
                Regards,<br>\
                Team Priyo\
            "

        elif email_type == "OTP_FORGOT":
            email_subject = "Code for Forget Password - Priyo"
            email_body = "Dear user,<br>\
                <br>\
                Your One Time Code for Priyo:<br>\
                <strong>" + otp + "</strong><br><br>\
                This code will be valid only for next 15 minutes.\
                If this was not you please ignore this email.<br>\
                you can always contact us at <a href='mailto:support@priyo.ru'>support@priyo.ru</a><br>\
                <br>\
                Regards,<br>\
                Team Priyo\
            "

        elif email_type == "OTP_VERIFY":
            email_subject = "Welcome to Priyo - Code for Verification"
            email_body = "Dear user,<br>\
                <br>\
                We are happy to see you on Priyo, below is your code to verify your email.<br>\
                Your One Time Code for Priyo:<br>\
                <strong>" + otp + "</strong><br><br>\
                This code will be valid only for next 15 minutes. \
                If this was not you please ignore this email.<br>\
                you can always contact us at <a href='mailto:support@priyo.ru'>support@priyo.ru</a><br>\
                <br>\
                Regards,<br>\
                Team Priyo\
            "
        elif email_type == "PASSWORD_RESET":
            email_subject = "Your password was reset - Priyo"
            email_body = "Dear user,<br>\
                <br>\
                Your password for Priyo has been changed<br>\
                <strong> If this was no done by you, then change the password immediately.</strong>\
                you can always contact us at <a href='mailto:support@priyo.ru'>support@priyo.ru</a><br>\
                <br>\
                Regards,<br>\
                Team Priyo\
            "
        else:
            logger.error("EMAIL_TYPE Mismatch")
            return
        
        subscriber = Profile.objects.get(id=profile_id)
        # email_body.replace("[first_name]", subscriber.name.split(" ")[0])

        email = EmailMessage(
            subject=email_subject,
            body=email_body,
            from_email="no-reply@priyo.ru",
            to=[subscriber.user.email]
        )
        email.content_subtype = "html"
        email.send()
    except Exception as err:
        logger.error(err)
        self.retry(exc=err, max_retries=3)

