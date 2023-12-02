from rest_framework import serializers
from .models import Chat


class MessageSerializer(serializers.ModelSerializer):
    self_sender = serializers.BooleanField(default=False, read_only=True)
    class Meta:
        model = Chat
        fields = "__all__"


class ChatProfileSerializer(serializers.Serializer):
    match_id = serializers.UUIDField()
    profile_id = serializers.UUIDField()
    name = serializers.CharField()
    age = serializers.IntegerField()
    profile_pic = serializers.ImageField()
    matched_on = serializers.DateTimeField()
    messages = serializers.ListField()

class OldMessageQuerySerializer(serializers.Serializer):
    last_page = serializers.DateTimeField()
    per_page = serializers.IntegerField(required=False, default=30)
