from rest_framework.response import Response
from rest_framework import viewsets
from .serializers import LocationSerializer
from rest_framework import status

from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated


# Create your views here.


class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get_queryset(self):
        return self.request.user.userprofile.location

    def perform_create(self, serializer):
        serializer.save(user=self.request.user.userprofile)

    def location_details(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def update(self, request):
        location = self.request.user.userprofile.location
        serializer = self.get_serializer(location, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request):
        location = self.request.user.userprofile.location
        location.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
