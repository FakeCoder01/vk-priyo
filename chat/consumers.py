import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "priyo.settings")

import json, datetime, logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from core.models import Profile
from django.shortcuts import get_object_or_404
from .models import Match, Chat
from .serializers import MessageSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from uuid import UUID
from urllib.parse import parse_qsl
from asgiref.sync import async_to_sync





logger = logging.getLogger(__name__)

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj) :
        try:
            if isinstance(obj, UUID):
                return obj.hex
            return json.JSONEncoder.default(self.obj)
        except:
            return    



"""
SOCKET PARAMS ON CONNECT : Auth Token, userID

for image:
    "image" : "image_url"

for text mesage:
    "message" : "text"

"""



class ChatConsumer(AsyncWebsocketConsumer):


    @database_sync_to_async
    def verify_and_get_user(self, user_auth_token):
        try:
            return Token.objects.get(key=user_auth_token).user
        except Exception as err:
            logger.error(err)
            self.close()
            return


    async def connect(self):
        query_params = dict(parse_qsl(self.scope['query_string'].decode('utf-8')))
        user_auth_token = query_params.get('token', None)
        profile_id = query_params.get('id', None)

        if user_auth_token == None or profile_id == None:
            self.close()


        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.user = await self.verify_and_get_user(user_auth_token)
        if not self.get_match():
            await self.close()

        await self.channel_layer.group_add(self.match_id, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
       
        try:
            if data.get('message', None) is not None:
                new_chat = await self.save_message(data.get('message'))

                await self.channel_layer.group_send(self.match_id, {
                    "type" : "chat_message_handler",
                    "message" : {
                        "type" : "message",
                        "data" : new_chat,
                        "status_code" : 200
                    },
                })

            elif data.get('image', None) is not None and data.get('sender', None) is not None and data.get('message_id', None) is not None:


                new_chat = await self.get_message(data.get('message_id'))
                await self.channel_layer.group_send(self.match_id, {
                    "type" : "chat_message_handler",
                    "message" : {
                        "type" : "image",
                        "data" : new_chat,
                        "status_code" : 200
                    },
                })
                
            else:
                return self.send_chat_message({
                    "type" : "error",
                    "status_code" : 400
                })
        except Exception as err:
            logger.error(err)


            
    async def send_chat_message(self, message):
        await self.send(text_data=json.dumps(message, cls=UUIDEncoder))

    @database_sync_to_async
    def get_match(self):
        return Match.objects.filter(Q(id=self.match_id) & ( Q(first_user=self.user.userprofile) | Q(second_user= self.user.userprofile) )).exists()

    @database_sync_to_async
    def save_message(self, message):
        chat = Chat.objects.create(
            match_id = self.match_id,
            sender = self.user.userprofile,
            message = message
        )
        serializer = MessageSerializer(chat)
        return serializer.data


    @database_sync_to_async
    def get_message(self, message_id):
        serializer = MessageSerializer(Chat.objects.get(message_id=message_id))  
        return serializer.data
    

    async def chat_message_handler(self, event):
        message = event['message']
        return await self.send(text_data=json.dumps(message, cls=UUIDEncoder))
        
