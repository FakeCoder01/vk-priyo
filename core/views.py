from rest_framework.response import Response
from rest_framework import viewsets, status
from .models import Profile, User, OTPVerify, Preference, Question, Location, LeftSwipe
from .serializers import ProfileSerializer, UserSerializer, OTPVerificationSerializer, PasswordResetSerializer

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, render
import random, logging

from google.oauth2 import id_token
from google.auth.transport.requests import Request

from celery import group
from .email_service import send_otp_via_email

from django.shortcuts import HttpResponse
# Create your views here.


logger = logging.getLogger(__name__)

class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get_queryset(self):
        return Profile.objects.get(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def profile_details(self, request, id=None):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=self.request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            logger.error(err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, id=None):
        try:
            queryset = Profile.objects.filter(user=self.request.user)
            profile = get_object_or_404(queryset, user=self.request.user)
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as err:
            logger.error(err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def destroy(self, request, id=None):
        try:
            if id == None:
                id = request.data.get('id')
            queryset = Profile.objects.filter(user=self.request.user)
            profile = get_object_or_404(queryset, id=id)
            profile.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as err:
            logger.error(err)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def set_csrf_token(request):
    csrf_token = get_token(request)
    return Response({'csrf_token':csrf_token}, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def sign_up(request):
    try:
        serializer = UserSerializer(data=request.data)
        if request.data.get('confirm_password') != request.data.get('password'):
            return Response({'detail': 'password not match'}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            user = User.objects.create_user(
                username = request.data.get('username'),
                password = request.data.get('password'),
                email = request.data.get('username'),
                is_active = False    # set False if email auth is needed
            )
            preference = Preference.objects.create()
            question = Question.objects.create()
            location = Location.objects.create()
            profile = Profile.objects.create(
                user = user,
                location = location,
                question = question,
                preference = preference
            )
            left_swipe = LeftSwipe.objects.create(user=profile)
            email_code = random.randint(100000, 999999)
            otp_profile = OTPVerify.objects.create(user=user)
            otp_profile.set_email_otp(str(email_code))
            otp_profile.save()

            send_otp_via_email.delay("OTP_VERIFY", str(profile.id), str(email_code))

            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token' : token.key, 'message': 'otp sent', 'next' : 'verify'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        logger.error(err)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def otp_verification(request):
    try:
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email_otp = request.data.get('email_otp')
            email = request.data.get('email')
            # set is_active to False at user creation if email auth is needed
            if not User.objects.filter(email=request.data.get('email'), is_active=False).exists():
                return Response({'detail' : 'error'}, status=status.HTTP_404_NOT_FOUND)
            user_otp = OTPVerify.objects.get(user=User.objects.get(email=request.data.get('email'), is_active=False))
            if not user_otp.verify_email(str(email_otp)):
                return Response({'detail' : 'otp mismatch'}, status=status.HTTP_400_BAD_REQUEST)
            
            user_otp.email_otp = ''
            user_otp.save()

            user = user_otp.user
            user.username = email
            user.email = email
            user.is_active = True
            user.save()
            return Response({'detail' : 'verification successful', 'next' : 'setup'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        logger.error(err)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def google_login_and_signup(request):
    token = request.data.get('id_token')
    try:
        idinfo = id_token.verify_oauth2_token(token, Request())
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        user_email = idinfo['email']
    except ValueError:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        if not User.objects.filter(username=user_email).exists():
            user = User.objects.create(email=user_email, username=user_email)
            preference = Preference.objects.create()
            question = Question.objects.create()
            location = Location.objects.create()
            profile = Profile.objects.create(
                user = user,
                location = location,
                question = question,
                preference = preference
            )
            left_swipe = LeftSwipe.objects.create(user=profile)
            otp_profile = OTPVerify.objects.create(user=user, is_email_verified = True)
        user = User.objects.get(username=user_email)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
 
        
    
@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def login_validation(request):
    try:
        return Response({
            "profile_id" : request.user.userprofile.id
        }, status=status.HTTP_200_OK)
    except Exception as err:
        logger.error(err)
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:

        auth_token = request.data.get('token', None)
        user = request.user

        if auth_token is not None and Token.objects.filter(key=auth_token, user=user).exists():
            Token.objects.filter(key=auth_token, user=user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as err:
        print(err)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    
def index_view(request):

    if request.GET.get("token", None) is None:
        return HttpResponse("Token required", status=status.HTTP_400_BAD_REQUEST)
    if request.GET.get("match", None) is None:
        return HttpResponse("Match required", status=status.HTTP_400_BAD_REQUEST)
    
    try:
        userid = Token.objects.get(key=request.GET.get("token")).user.userprofile.id
    except:
        return HttpResponse("User not found", status=status.HTTP_404_NOT_FOUND)
    context = {
        "auth_token" : request.GET.get("token"),
        "user_id" : str(userid).replace("-", ""),
        "match_id" : request.GET.get("match") 
    }
    return render(request, 'file.htm', context)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def forget_password(request):
    try:
        serializer = PasswordResetSerializer(data=request.data)

        if serializer.is_valid():
            email = request.data.get('email')
            email_otp = request.data.get('email_otp')
            password = request.data.get('password')
            confirm_password = request.data.get('confirm_password')

            if not User.objects.filter(email=email, username=email).exists():
                return Response({
                    "detail" : "user not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            user =  User.objects.get(email=email, username=email)
            user.is_active = True
            user.save()
            user_otp = OTPVerify.objects.get(user=user)

            if not user_otp.verify_email(str(email_otp)):
                return Response({'detail' : 'otp mismatch'}, status=status.HTTP_400_BAD_REQUEST)
            
            user_otp.email_otp = ''
            user_otp.save()

            if password != confirm_password:
                return Response({'detail' : 'password not same'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(password)
            user.save()
            send_otp_via_email.delay(email_type="PASSWORD_RESET", profile_id=str(user.userprofile.id), otp="")
            return Response({'detail' : 'password reset', 'next' : 'login'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        logger.error(err)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def send_otp(request):
    try:
        email = request.data.get('email', None)
        if email is None or not User.objects.filter(email=email, username=email).exists():
            return Response({
                "detail" : "otp sent."
            }, status=status.HTTP_404_NOT_FOUND)
    
        user = User.objects.get(email=email, username=email)
        user_otp = OTPVerify.objects.get(user=user)
        email_code = random.randint(100000, 999999)
        user_otp.set_email_otp(str(email_code))
        user_otp.save()
        if request.data.get('send_type', None) == "forget":
            send_otp_via_email.delay("OTP_FORGOT", str(user.userprofile.id), str(email_code))
        else:
            send_otp_via_email.delay("OTP_RESEND", str(user.userprofile.id), str(email_code))

        return Response({'detail' : 'otp sent'}, status=status.HTTP_200_OK)
    except Exception as err:
        logger.error(err)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
