from core.models import Profile, LeftSwipe, RightSwipe, Match
from .serializers import RecommendProfileSerializer

from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from django.db.models import Value, IntegerField, Q
from rest_framework.response import Response

import math, logging
from fuzzywuzzy import fuzz
from collections import defaultdict


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


class RecommendProfiles(viewsets.ModelViewSet):
    serializer_class = RecommendProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get_queryset(self):
        return self.request.user.userprofile
    
    def get_recommendations(self, request):
        try:
            user_profile = self.request.user.userprofile
            user_preference = user_profile.preference       # retrieve user preferences
            user_location = user_profile.location           # retrieve user location
            user_tags = user_profile.tags.all()             # retrieve user tags
            user_questions = user_profile.question          # retrieve user question

            # Retrieve user left-swiped profiles
            left_swipes = LeftSwipe.objects.get(user=user_profile).disliked_users.all() # if LeftSwipe.objects.filter(
            #  user=user_profile).exists() else []

            # Retrieve user right-swiped profiles
            right_swipes = RightSwipe.objects.filter(whom_liked=user_profile)

            # Retrive user matches
            matches = Match.objects.filter(Q(first_user=user_profile) | Q(second_user=user_profile))


            lat_min = user_location.lat - (MAX_DISTANCE / 111.0)
            lat_max = user_location.lat + (MAX_DISTANCE / 111.0)
            lng_min = user_location.lng - (MAX_DISTANCE / (111.0 * math.cos(math.radians(user_location.lat))))
            lng_max = user_location.lng + (MAX_DISTANCE / (111.0 * math.cos(math.radians(user_location.lat))))

            # Filter profiles based on proximity
            nearby_profiles = Profile.objects.filter(
                location__lat__range=(lat_min, lat_max),
                location__lng__range=(lng_min, lng_max)
            ).exclude(user=self.request.user).exclude(id__in=matches).exclude(id__in=left_swipes).annotate(distance=Value(10, output_field=IntegerField()))

            # calculate similarity scores
            potential_matches = defaultdict(int)
            for profile in nearby_profiles:
                # check if the userprofile is verified
                # verified params are 
                # - OTP, Photo (needs to be implemented)
                profile_of_user = profile.user
                try:
                    if not profile_of_user.userotp.is_email_verified:
                        continue
                except Exception as err:
                    logger.error(err)
                    logger.info("User account not verified [recommender.py]")
                    continue

                similarity_score = 0
                # compare gender preference (strict)
                try:
                    if user_preference.gender_preference == profile.gender and user_profile.gender == profile.preference.gender_preference:
                        similarity_score += 1
                    elif user_preference.gender_preference == "Both":
                        similarity_score += 1
                    else:
                        continue    
                except Exception as err:
                    logger.error(err)
                    logger.info("User and/or Profile doesn't have a gender")
                    continue

                # compare age preferences (strict)
                try:
                    if (user_preference.min_age_preference <= profile.age <= user_preference.max_age_preference) and (
                        profile.preference.min_age_preference <= user_profile.age <= profile.preference.max_age_preference):
                        similarity_score += 2
                    else:
                        continue
                except Exception as err:
                    logger.error(err)
                    logger.info("User and/or Profile doesn't have an gae specified")
                    continue

                # compare dating radius (strict)
                try:
                    if user_location and profile.location:
                        distance = calculate_distance(user_location.lat, user_location.lng, profile.location.lat, profile.location.lng)
                        if distance <= user_preference.dating_radius:
                            similarity_score += (10 - (distance * 0.1)) 
                            profile.distance = int(distance)
                        else:
                            continue    
                except Exception as err:
                    logger.error(err)
                    logger.info("User and/or Profile doesn't have a dating radius specified")
                    continue

                try:
                    about_match_ratio = fuzz.ratio(user_profile.bio.lower(), profile.bio.lower())
                    similarity_score += (about_match_ratio * 0.1)
                except Exception as err:
                    logger.error(err)
                    logger.info("User and/or Profile doesn't have a bio specified")

                

                # implement ml here



                # compare dating reason
                try:
                    if user_preference.here_for and profile.preference.here_for and user_preference.here_for == profile.preference.here_for:
                        similarity_score += 2
                except Exception as err:
                    logger.error(err)
                    logger.info("User and/or Profile doesn't have a Reason (here_for) specified")


                try:
                    city_match_ratio = fuzz.ratio(user_location.city.lower(), profile.location.city.lower())
                    similarity_score += (city_match_ratio * 0.3)
                except Exception as err:
                    logger.error(err)
                    logger.info("User and/or Profile hasn't a city specified")

                # compare tags
                profile_tags = profile.tags.all()
                common_tags = user_tags.intersection(profile_tags)
                similarity_score += len(common_tags)

                # Compare answers to questions
                profile_questions = profile.question
                if user_questions and profile_questions:
                    try:
                        fav_song_ratio = fuzz.ratio(user_questions.fav_song.lower(), profile_questions.fav_song.lower())
                        similarity_score += (fav_song_ratio * 0.1)
                    except Exception as err:
                        logger.info("User and/or Profile doesn't have a fav song specified")
                    try:
                        zodiac_sign_ratio = fuzz.ratio(user_questions.zodiac_sign.lower(), profile_questions.zodiac_sign.lower())
                        similarity_score += (zodiac_sign_ratio * 0.5)
                    except:
                        logger.info("User and/or Profile doesn't have a zodiac sign specified")
                    try:
                        if user_questions.drinking == profile_questions.drinking:
                            similarity_score += 1
                    except:
                        logger.info("User and/or Profile doesn't have drinking specified")
                    try:
                        if user_questions.smoking == profile_questions.smoking:
                            similarity_score += 1
                    except:
                        logger.info("User and/or Profile doesn't have smoking specified")
                    try:
                        religion_ratio = fuzz.ratio(user_questions.religion.lower(), profile_questions.religion.lower())
                        similarity_score += (religion_ratio * 0.1)
                    except:
                        logger.info("User and/or Profile doesn't have a religion specified")
                    try:
                        languages_ratio = fuzz.ratio(user_questions.languages.lower(), profile_questions.languages.lower())
                        similarity_score += (languages_ratio * 0.05)
                    except:
                        logger.info("user and/or Profile doesn't have languages specified")
                    try:
                        if user_questions.height - 10 <= profile_questions.height <= user_questions.height + 10 :
                            similarity_score += 1
                    except:
                        logger.info("User and/or Profile doesn't have height specified")    
                    try:
                        if user_questions.body_type == profile_questions.body_type:
                            similarity_score += 2
                    except:
                        logger.info("User and/or Profile doesn't have body type specified")
                    try:
                        profession_ratio = fuzz.ratio(user_questions.profession.lower(), profile_questions.profession.lower())
                        similarity_score += (profession_ratio * 0.04)
                    except:
                        logger.info("User and/or Profile doesn't have a profession specified")
                    try:
                        place_ratio = fuzz.ratio(user_questions.place.lower(), profile_questions.place.lower())
                        similarity_score += (place_ratio * 0.08)
                    except:
                        logger.info("User and/or Profile doesn't have a place of work specified")

                if profile.pk in right_swipes:
                    similarity_score += 5

                if similarity_score >= SIMILARITY_THRESHOLD:
                    potential_matches[profile] += similarity_score
            # sort potential matches by similarity score
            potential_matches = sorted(potential_matches.items(), key=lambda x: x[1], reverse=True)
            # get recommended profiles
            recommended_profiles = [profile for profile, _ in potential_matches[:MAX_RECOMMENDATIONS]]
            serializer = self.get_serializer(recommended_profiles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as err:
            logger.error(err)
            logger.info("EDGE CASE")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR) 