from rest_framework import serializers
from core.models import (
    Match, LeftSwipe, 
    RightSwipe, Profile, Tag,
    ReportProfile
)
from core.serializers import QuestionSerializer


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = "__all__"

class LeftSwipeSerializer(serializers.ModelSerializer):
    profile_id = serializers.CharField(source="Profile.id")
    class Meta:
        model = LeftSwipe
        fields = ("profile_id",)     


class RightSwipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RightSwipe
        fields = ("whom_liked", )  

class TagSerializer(serializers.ModelSerializer):
    selected = serializers.BooleanField(read_only=True, default=False)
    class Meta:
        model = Tag
        fields = ("id", "name", "icon", "selected")

class RecommendProfileSerializer(serializers.ModelSerializer):
    city = serializers.CharField(source="location.city")
    tag_names = TagSerializer(source='tags', read_only=True, many=True)
    questions = QuestionSerializer(source="question", read_only=True)
    here_for = serializers.CharField(source="preference.here_for")
    images = serializers.SerializerMethodField()
    distance = serializers.IntegerField(read_only=True)

    class Meta:
        model = Profile        
        fields = ("id", "name", "images", "age", "gender", "bio", "city", "tag_names", "questions","here_for", "distance")

    def get_images(self, obj):
        images = [img.image.url for img in obj.userimg.all()]
        return images

class ReportProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportProfile
        fields = "__all__"