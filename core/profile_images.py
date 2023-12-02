from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import Profile, ProfileImage
from rest_framework import status
from .serializers import ImageUploadSerializer, EditProfilePageImageSerializer, ImageParseSerializer
from face.face_verification import image_upload_face_verificationn, profile_picture_face_verification

@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def profile_pic_upload(request):
    if "profile_pic" in request.FILES:

        image = request.FILES['profile_pic']
        p = Profile.objects.get(user=request.user)
        p.profile_pic = image
        p.save()
        """
            ### image validation
                - only one face
                - no face match with existing users
                - use this face to verify further photos
                - no vulgur or spam photo
        """
        if profile_picture_face_verification(p.id):
            serializer = ImageParseSerializer(p)
            return Response(serializer.data, status=status.HTTP_200_OK)
            # return Response({
            #     'message': 'profile pic uploaded',
            #     'profile_pic' : p.profile_pic
            # }, status=status.HTTP_200_OK)
        else:
            p.profile_pic.delete(save=True)
            return Response({"message" : "profile picture verification failed"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    return Response({"detail" : "image invalid"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def profile_image_upload(request):
    serializer = ImageUploadSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user.userprofile)
        """
            ### image validation
                - at least one face matches with profile picture
                - no vulgur or spam photo
        """
        if image_upload_face_verificationn(serializer.data.get('id')):
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            serializer.delete.save(save=True)
            return Response({"message" : "image upload verification failed"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def profile_image_delete(request, id:str):
    if ProfileImage.objects.filter(id=id, user=request.user.userprofile).exists():
        ProfileImage.objects.get(id=id, user=request.user.userprofile).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({"detail" : "id invalid"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def edit_profile_get_images(request):
    images = ProfileImage.objects.filter(user=request.user.userprofile)
    serializer = EditProfilePageImageSerializer(images, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
