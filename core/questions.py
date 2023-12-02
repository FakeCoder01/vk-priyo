from rest_framework.response import Response
from rest_framework import viewsets
from .serializers import QuestionSerializer
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated


import logging


# Create your views here.


logger = logging.getLogger(__name__)


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get_queryset(self):
        return self.request.user.userprofile.question

    def perform_create(self, serializer):
        serializer.save()

    def question_details(self, request, id=None):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

    def update(self, request, id=None):
        try:
            question = self.request.user.userprofile.question
            serializer = self.get_serializer(question, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            logger.error(err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, id=None):
        question = self.request.user.userprofile.question
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
