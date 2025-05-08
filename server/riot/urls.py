from django.urls import path
from . import views

urlpatterns = [
    path('', views.summoner_profile, name='profile_form'),
    path('get-riot-matches/', views.RiotMatchesView.as_view(), name='get_riot_matches'),
    path('riot/matches/', views.RiotMatchesView.as_view(), name='riot_matches'),
]