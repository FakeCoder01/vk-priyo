from django.urls import path
from .views import LeftSwipeViewSet, RightSwipeViewSet, TagViewSet
from .recomender import RecommendProfiles
from .reports import ReportProfileViewSet
from . import match
from .profile_data import ProfileDataViewSet

urlpatterns = [

    path("swipe/left/", LeftSwipeViewSet.as_view({
        "get" : "swipe_details",
        "post" : "perform_create",
        "put" : "update",
        "delete" : "destroy",
    }), name="left_swipe_view_set"),

    path("swipe/right/", RightSwipeViewSet.as_view({
        "get" : "swipe_details",
        "post" : "perform_create",
        "put" : "update",
        "delete" : "destroy",
    }), name="right_swipe_view_set"),

    path("recommend/", RecommendProfiles.as_view({
        "get" : "get_recommendations",
        "post" : "get_recommendations",
    }), name="recommend_profiles"),

    path("tags/", TagViewSet.as_view({
        'get' : 'tags'
    }), name="tags_view_set"),

    path("report/profile/", ReportProfileViewSet.as_view({
        "post" : "create"
    }), name="report_profile_view_set"),


    path("match/<str:match_id>/", match.delete_match, name="delete_match"),

    path("profile/<str:profile_id>/", ProfileDataViewSet.as_view({
        "get" : "get_profile_data"
    }), name="profile_data_view_set"),
    
]