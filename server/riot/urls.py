from django.urls import path
from . import views

urlpatterns = [
    path('', views.summoner_profile, name='profile_form'),
    path('get-riot-matches/', views.RiotMatchesView.as_view(), name='get_riot_matches'),
    path('match-details/', views.match_details, name='match_details'),
    path('download-csv/', views.download_match_csv, name='download_match_csv'),  # New URL for CSV download
]