from django.urls import path, include
from . import views

urlpatterns = [
    path('match/', views.all_chat_messages, name="all_chat_messages"),
    path('match/<str:match_id>/', views.chat_profile_message, name="chat_profile_message"),
    path('match/<str:match_id>/older/', views.older_chat_message, name="older_chat_message"),
    path('match/<str:match_id>/upload/image/', views.upload_image_to_chat, name="upload_image_to_chat"),
]