from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import LeftSwipeSerializer, RightSwipeSerializer, TagSerializer
from core.models import Match, LeftSwipe, RightSwipe, Profile, Tag

from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Value, BooleanField



import logging


logger = logging.getLogger(__name__)

# Create your views here.

class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def tags(self, request):
        tag_list = Tag.objects.all()
        tag_list_serializer = self.get_serializer(tag_list, many=True)
        tags = request.user.userprofile.tags.annotate(selected=Value(True, output_field=BooleanField()))
        tags_serializer = self.get_serializer(tags, many=True)
        return Response({
            "tag_list" : tag_list_serializer.data,
            "tags" : tags_serializer.data
        }, status=status.HTTP_200_OK)


class LeftSwipeViewSet(viewsets.ModelViewSet):

    serializer_class = LeftSwipeSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get_queryset(self):
        return LeftSwipe.objects.get(user=self.request.user.userprofile)

    def perform_create(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            if not request.data.get('profile_id') or not Profile.objects.filter(id=request.data.get('profile_id')).exists():
                return Response({'message': 'user not exits'}, status=status.HTTP_404_NOT_FOUND)
            left_swiped_user = Profile.objects.get(id=request.data.get('profile_id'))
            if left_swiped_user == self.request.user.userprofile:
                return Response({'message': 'can not left swipe yourself'}, status=status.HTTP_403_FORBIDDEN)
            if serializer.is_valid():
                LeftSwipe.objects.get(user=self.request.user.userprofile).disliked_users.add(left_swiped_user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            logger.error(err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request):
        return Response(status=status.HTTP_200_OK)
    
    def swipe_details(self, request):
        return Response(status=status.HTTP_200_OK)
    
    def destroy(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)
    


class RightSwipeViewSet(viewsets.ModelViewSet):

    serializer_class = RightSwipeSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get_queryset(self):
        return RightSwipe.objects.get(user=self.request.user.userprofile)
    

    """
        A 201 status code means it got a match
        A 200 means it added the right swipe
    """
    def perform_create(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            if not request.data.get('whom_liked') or not Profile.objects.filter(id=request.data.get('whom_liked')).exists():
                return Response({'message': 'user not exits'}, status=status.HTTP_404_NOT_FOUND)
            right_swiped_user = Profile.objects.get(id=request.data.get('whom_liked'))
            if right_swiped_user== self.request.user.userprofile:
                return Response({'message': 'can not right swipe yourself'}, status=status.HTTP_403_FORBIDDEN)
            if RightSwipe.objects.filter(user=self.request.user.userprofile, whom_liked=right_swiped_user).exists():
                match = Match.objects.get(first_user=self.request.user.userprofile, second_user=right_swiped_user)
                return Response({
                    "message" : "match-old",
                    "match_id" : match.id,
                    "name" : right_swiped_user.name,
                    "img" : str(right_swiped_user.profile_pic),
                    "age" : right_swiped_user.age,
                    "own_img" : str(self.request.user.userprofile.profile_pic),
                    "city" : right_swiped_user.location.city
                }, status=status.HTTP_201_CREATED) # got a match
            
                # return Response({'message' : 'already right swiped'}, status=status.HTTP_403_FORBIDDEN)
            
            if serializer.is_valid():

                RightSwipe.objects.create(
                    user=self.request.user.userprofile,
                    whom_liked = right_swiped_user
                )

                if RightSwipe.objects.filter(user=right_swiped_user, whom_liked=self.request.user.userprofile).exists():
                    match = Match.objects.create(
                        first_user = self.request.user.userprofile,
                        second_user = right_swiped_user
                    )
                    return Response({
                        "message" : "match",
                        "match_id" : match.id,
                        "name" : right_swiped_user.name,
                        "img" : str(right_swiped_user.profile_pic),
                        "age" : right_swiped_user.age,
                        "own_img" : str(self.request.user.userprofile.profile_pic),
                        "city" : right_swiped_user.location.city
                    }, status=status.HTTP_201_CREATED)
                
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            logger.error(err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR00)
        
        
    def update(self, request):
        return Response(status=status.HTTP_200_OK)
    
    def swipe_details(self, request):
        return Response(status=status.HTTP_200_OK)
    
    def destroy(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)
        