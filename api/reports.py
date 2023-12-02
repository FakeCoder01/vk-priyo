from rest_framework.response import Response
from rest_framework import viewsets
from .serializers import ReportProfileSerializer
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
import logging

# Create your views here.


logger = logging.getLogger(__name__)

class ReportProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ReportProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def create(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            logger.error(err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)