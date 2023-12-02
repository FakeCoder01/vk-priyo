from rest_framework.response import Response
from rest_framework import viewsets
from .serializers import PreferenceSerializer
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

# Create your views here.


class PreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = PreferenceSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get_queryset(self):
        return self.request.user.userprofile.preference

    def perform_create(self, serializer):
        serializer.save()

    def preference_details(self, request, id=None):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def update(self, request, id=None):
        preference = self.request.user.userprofile.preference
        serializer = self.get_serializer(preference, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, id=None):
        preference = self.request.user.userprofile.preference
        preference.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
