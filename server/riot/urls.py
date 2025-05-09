from django.urls import path
from . import views

urlpatterns = [
    path('', views.summoner_profile, name='profile_form'),
    path('get-riot-matches/', views.RiotMatchesView.as_view(), name='get_riot_matches'),
    # path('riot/matches/', views.RiotMatchesView.as_view(), name='riot_matches'),
    # path('matches-detail/', views.RiotMatchesView.as_view(), name='match_details'),
    path('match-details/', views.match_details, name='match_details'),
]