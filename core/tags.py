from rest_framework.response import Response
from rest_framework import viewsets
from .models import Tag
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
# Create your views here.


class TagManageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def create(self, request):
        if request.data.get('id') != '' and Tag.objects.filter(id=str(request.data.get('id'))).exists():
            tag = Tag.objects.get(id=str(request.data.get('id')))
            profile = self.request.user.userprofile
            profile.tags.add(tag)
            return Response({"details" : "tag added"}, status=status.HTTP_201_CREATED)
        return Response({"detail" : "All fields are neccessary"}, status=status.HTTP_400_BAD_REQUEST)
    
        
    def destroy(self, request):
        if request.data.get('id') != '' and Tag.objects.filter(id=str(request.data.get('id'))).exists():
            tag = Tag.objects.get(id=str(request.data.get('id')))
            profile = self.request.user.userprofile
            profile.tags.remove(tag)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail" : "All fields are neccessary"}, status=status.HTTP_400_BAD_REQUEST)
