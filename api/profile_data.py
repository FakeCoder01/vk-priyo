from core.models import Profile
from .serializers import RecommendProfileSerializer

from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from django.db.models import Value, IntegerField
from rest_framework.response import Response

import math, logging



# logger initialization
logger = logging.getLogger(__name__)

# constants
SIMILARITY_THRESHOLD = 10
MAX_RECOMMENDATIONS = 32
MAX_DISTANCE = 100

def calculate_distance(lat1, lng1, lat2, lng2):
    # calculate the distance between two sets of latitude and longitude coordinates
    # using the Haversine formula to calculate distance   
    R = 6371  # radius of the earth in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *  math.sin(dlng / 2) * math.sin(dlng / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


class ProfileDataViewSet(viewsets.ModelViewSet):
    serializer_class = RecommendProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get_queryset(self):
        return self.request.user.userprofile
    
    def check_if_profile_exists(self):
        return Profile.objects.filter(id=self.id).exists
    
    def get_profile_data(self, request, profile_id):
        try:
            self.id = profile_id
            if not self.check_if_profile_exists():
                return Response(status=status.HTTP_404_NOT_FOUND)

            profile = Profile.objects.filter(id=profile_id).annotate(distance=Value(100, output_field=IntegerField()))[0]

            user_lat = self.request.user.userprofile.location.lat
            user_lng = self.request.user.userprofile.location.lng

            profile_lng = profile.location.lng
            profile_lat = profile.location.lat

            distance = calculate_distance(user_lat, user_lng, profile_lat, profile_lng)
            profile.distance = round(distance)

            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as err:
            logger.error(err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)