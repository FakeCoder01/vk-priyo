from django.db import models
from core.models import Profile, Match
import uuid
# Create your models here.




class Chat(models.Model):
    message_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="match_chat", blank=True)
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="chat_sender", blank=True)
    message = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='chat/images/', null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        # return self.sender.name
        return str(self.message_id)