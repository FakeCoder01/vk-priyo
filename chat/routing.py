import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "priyo.settings")

from django.urls import re_path 
from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/chat/match/(?P<match_id>[^/]+)/$", consumers.ChatConsumer.as_asgi())
]
