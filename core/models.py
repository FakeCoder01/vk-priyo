import os
from django.db import models
from django.contrib.auth.models import User
import uuid, datetime
from django.contrib.auth.hashers import check_password, make_password

# Create your models here.


class Location(models.Model):
    lat = models.FloatField(blank=True, null=True)
    lng = models.FloatField(blank=True, null=True)
    address = models.CharField(max_length=150, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=32, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.id)

class Question(models.Model):
    fav_song = models.CharField(max_length=100, null=True, blank=True)
    fav_song_link = models.URLField(null=True, blank=True)
    zodiac_sign = models.CharField(max_length=16, null=True, blank=True)
    drinking = models.CharField(max_length=8, null=True, blank=True)
    smoking = models.BooleanField(default=False, null=True, blank=True)
    religion = models.CharField(max_length=10, null=True, blank=True)
    languages = models.CharField(max_length=32, null=True, blank=True)
    height = models.PositiveSmallIntegerField(null=True, blank=True)
    body_type = models.CharField(max_length=8, null=True, blank=True)
    profession = models.CharField(max_length=8, default="Student")
    place = models.CharField(max_length=32, null=True, blank=True)

    def __str__(self) -> str:
        return str(self.id)

class Tag(models.Model):
    icon = models.ImageField(upload_to="static/tags/icons/", null=True, blank=True)
    name = models.CharField(max_length=32)

    def __str__(self) -> str:
        # return self.name
        return str(self.id)
    

class Preference(models.Model):
    gender_preference = models.CharField(max_length=8, null=True, blank=True)
    min_age_preference = models.PositiveSmallIntegerField(null=True, blank=True)
    max_age_preference = models.PositiveSmallIntegerField(null=True, blank=True)
    dating_radius = models.FloatField(null=True, blank=True)
    here_for = models.CharField(max_length=8, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.id)

class Profile(models.Model):
    user = models.OneToOneField(User, related_name="userprofile", on_delete=models.CASCADE)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    profile_pic = models.ImageField(upload_to="static/user/dp/", null=True, blank=True)

    name = models.CharField(max_length=40, blank=True, null=True)
    gender = models.CharField(max_length=8, null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    age = models.PositiveSmallIntegerField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    location = models.OneToOneField(Location, related_name="userloc", on_delete=models.CASCADE, null=True, blank=True)
    question =  models.OneToOneField(Question, related_name="userques", on_delete=models.CASCADE, null=True, blank=True)
    preference = models.OneToOneField(Preference, related_name="userpref", on_delete=models.CASCADE, null=True, blank=True)
    tags = models.ManyToManyField(Tag, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # return self.user.email
        return str(self.id)
    
class ProfileImage(models.Model):
    user = models.ForeignKey(Profile, related_name="userimg", on_delete=models.CASCADE)
    caption = models.CharField(max_length=50, null=True, blank=True)
    image = models.ImageField(upload_to="static/user/images/")

    def __str__(self) -> str:
        return str(self.id)
    

class LeftSwipe(models.Model):
    user = models.OneToOneField(Profile, related_name="userdislike", on_delete=models.CASCADE)
    disliked_users = models.ManyToManyField(Profile)

    def __str__(self) -> str:
        # return self.user.user.username
        return str(self.id)

class RightSwipe(models.Model):
    user = models.ForeignKey(Profile, related_name="userlike", on_delete=models.CASCADE)
    whom_liked = models.ForeignKey(Profile, related_name="liked", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.id)

class Match(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)
    first_user = models.ForeignKey(Profile, related_name="f_user", on_delete=models.CASCADE)
    second_user = models.ForeignKey(Profile, related_name="s_user", on_delete=models.CASCADE)    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.id)

class OTPVerify(models.Model):
    user = models.OneToOneField(User, related_name="userotp", on_delete=models.CASCADE)
    is_email_verified = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=200, null=True, blank=True)
    email_otp_creation = models.DateTimeField(null=True, blank=True)

    def set_email_otp(self, code):
        self.email_otp = make_password(code)
        self.email_otp_creation = datetime.datetime.now()

    def verify_email(self, email_otp):
        #if  self.email_otp_creation > datetime.datetime.now() - datetime.timedelta(minutes=10):
        self.is_email_verified = True
        return check_password(email_otp, self.email_otp)
        #return False
    
    def __str__(self) -> str:
        # return self.user.username
        return str(self.id)
    
class ReportProfile(models.Model):

    reported = models.ForeignKey(Profile, related_name="reporteds", on_delete=models.CASCADE)
    reporter = models.ForeignKey(Profile, related_name="reporter", on_delete=models.CASCADE)

    is_reported = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=True)

    reason = models.CharField(max_length=200, null=True, blank=True)
    resolved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self) -> str:
        return str(self.id)
