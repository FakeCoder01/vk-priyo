from rest_framework.response import Response
from .models import Chat, Match, Profile
from core.models import ProfileImage
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Subquery, OuterRef, Q, When, Case, F
from rest_framework import status
from django.db import models
from .serializers import OldMessageQuerySerializer, MessageSerializer, ChatProfileSerializer
import logging


# Create your views here.


logger = logging.getLogger(__name__)


def get_profile_pic(profile:Profile):
    return ProfileImage.objects.filter(user=profile).first().image




@api_view(['GET'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def all_chat_messages(request):
    try:
        profile = request.user.userprofile
        last_messages = Chat.objects.filter(match=OuterRef('pk')).order_by('-sent_at')

        user_chat_groups = Match.objects.filter(Q(first_user=profile) | Q(second_user=profile)).distinct().annotate(
            message_id=Subquery(last_messages.values('message_id')[:1]),
            text_message=Subquery(last_messages.values('message')[:1]),
            image_message=Subquery(last_messages.values('image')[:1]),
            sent_at=Subquery(last_messages.values('sent_at')[:1]),
            other_user=Case(
                When(first_user=profile, then=F('second_user')),
                When(second_user=profile, then=F('first_user')),
                default=None,
                output_field=models.ForeignKey(Profile, on_delete=models.CASCADE)
            ),
            other_person_profile_picture=Subquery(
                ProfileImage.objects.filter(
                    user=OuterRef('other_user')
                ).values('image')[:1]
            )
        ).annotate(
            other_person_name=Case(
                When(first_user=profile, then=F('second_user__name')),
                When(second_user=profile, then=F('first_user__name')),
                default=None,
                output_field=models.CharField()
            )
        ).values(
            'id',
            'message_id',
            'other_person_name',
            'other_person_profile_picture',
            'text_message',
            'image_message',
            'sent_at',
        )
        return Response(list(user_chat_groups), status=status.HTTP_200_OK)
    except Exception as err:
        logger.error(err)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def older_chat_message(request, match_id:str):
    try:
        serializer = OldMessageQuerySerializer(data=request.query_params)
        if Match.objects.filter(Q(id=match_id) & ( Q(first_user=request.user.userprofile) | Q(second_user= request.user.userprofile) )).exists():
            match = Match.objects.get(id=match_id) 
            if serializer.is_valid(raise_exception=True):
                last_page = serializer.validated_data['last_page']
                per_page = serializer.validated_data['per_page']
                messages = Chat.objects.filter(sent_at__lt=last_page, match=match).order_by('-sent_at')[:per_page]
                serialized_messages = MessageSerializer(messages, many=True)
                return Response(serialized_messages.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    except Exception as err:
        logger.error(err)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def chat_profile_message(request, match_id:str):
    try:
        if Match.objects.filter(Q(id=match_id) & ( Q(first_user=request.user.userprofile) | Q(second_user= request.user.userprofile) )).exists():
            
            match = Match.objects.get(id=match_id) 
            person = match.first_user if match.second_user == request.user.userprofile else match.second_user
            messages = Chat.objects.filter(match=match).order_by('-sent_at')[:150].annotate(
                self_sender=Case(
                    When(sender=request.user.userprofile, then=True),
                    default = False,
                    output_field = models.BooleanField()
                )
            )
            serializer = ChatProfileSerializer(data={
                "match_id": match_id,
                "name": person.name,
                "profile_id": person.id,
                "profile_pic": get_profile_pic(person),
                "age": person.age,
                "matched_on" : match.created_at,
                "messages": MessageSerializer(messages, many=True).data
            })
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    except Exception as err:
        logger.error(err)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def upload_image_to_chat(request, match_id:str):
    try:
        if Match.objects.filter(Q(id=match_id) & ( Q(first_user=request.user.userprofile) | Q(second_user= request.user.userprofile) )).exists():
            serializer = MessageSerializer(data=request.data)
            if serializer.is_valid():
                match = Match.objects.get(id=match_id)
                serializer.save(match=match, sender=request.user.userprofile)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as err:
        logger.error(err)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
