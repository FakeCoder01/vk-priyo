from rest_framework import serializers
from .models import (
    Profile, User, Question,
    Preference, ProfileImage,
    Tag, Location, OTPVerify
)


class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField()
    class Meta:
        model = User
        fields = ('username', 'password', 'confirm_password')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "icon")

class ProfileSerializer(serializers.ModelSerializer):
    city = serializers.CharField(source="location.city", read_only=True)
    class Meta:
        model = Profile
        fields = "__all__"


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"

class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = "__all__"

class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileImage
        fields = "__all__"    

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"    

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"    

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.CharField(source="User.email")
    class Meta:
        model = OTPVerify
        fields = ("email_otp", "email")

class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileImage
        fields = ("id", "caption", "image",)


class EditProfilePageImageSerializer(serializers.ModelSerializer):
    key = serializers.IntegerField(source="id")
    url = serializers.ImageField(source="image")
    disabledDrag = serializers.BooleanField(default=False)
    disabledReSorted = serializers.BooleanField(default=False)

    class Meta:
        model = ProfileImage
        fields = ("key", "url", "disabledDrag", "disabledReSorted")


class ImageParseSerializer(serializers.Serializer):
    profile_pic = serializers.ImageField()

    class Meta:
        fields = ("profile_pic",)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    email_otp = serializers.IntegerField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()