from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Match
from rest_framework import status
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def delete_match(request, match_id:str):
    try:
        if Match.objects.filter( Q(id=match_id) & ( Q(first_user=request.user.userprofile) | Q(second_user=request.user.userprofile)) ).exists() :
            Match.objects.get(id=match_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail" : "id invalid"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        logger.error(err)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)