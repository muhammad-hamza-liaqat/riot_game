# from django.http import JsonResponse
# from django.views import View
# from django.shortcuts import render
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator
# from django.conf import settings
# import requests
# import datetime
# import json

# def summoner_profile(request):
#     return render(request, 'index.html')

# @method_decorator(csrf_exempt, name='dispatch')
# class RiotMatchesView(View):
#     def post(self, request):
#         try:
#             data = json.loads(request.body)

#             summoner_name = data.get('summoner_name')
#             region = data.get('region', 'NA1').upper()
#             language = data.get('language', 'en_US')

#             if not summoner_name or not region:
#                 return JsonResponse({'error': 'Summoner name and region are required'}, status=400)

#             api_key = settings.RIOT_API_KEY
#             print(f"API Key:-------------------> {api_key}")
#             headers = {'X-Riot-Token': api_key}

#             account_url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner_name}/{region}'
#             account_response = requests.get(account_url, headers=headers)

#             # if account_response.status_code != 200:
#             #     return JsonResponse({'error': 'Failed to fetch account data'}, status=account_response.status_code)

#             puuid = account_response.json().get('puuid')
#             if not puuid:
#                 return JsonResponse({'error': 'PUUID not found'}, status=404)

#             match_ids_url = f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids'
#             match_ids_response = requests.get(match_ids_url, headers=headers)

#             if match_ids_response.status_code != 200:
#                 return JsonResponse({'error': 'Failed to fetch match IDs'}, status=match_ids_response.status_code)

#             match_ids = match_ids_response.json()
#             if not match_ids:
#                 return JsonResponse({'error': 'No matches found'}, status=404)

#             match_url = f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_ids[0]}'
#             match_response = requests.get(match_url, headers=headers)

#             if match_response.status_code != 200:
#                 return JsonResponse({'error': 'Failed to fetch match details'}, status=match_response.status_code)

#             match_data = match_response.json()
#             match_timestamp = match_data['info']['gameCreation'] / 1000
#             match_datetime = datetime.datetime.utcfromtimestamp(match_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')

#             match_data_json = json.dumps(match_data, indent=2)

#             response_data = {
#                 'summoner_name': summoner_name,
#                 'region': region,
#                 'language': language,
#                 'puuid': puuid,
#                 'match_id': match_ids[0],
#                 'match_date': match_datetime,
#                 'match_data': match_data,
#                 'match_data_json': match_data_json
#             }

#             return render(request, 'match_details.html', {'response_data': response_data})

#         except requests.RequestException as e:
#             return JsonResponse({'error': f'API request failed: {str(e)}'}, status=500)
#         except Exception as e:
#             return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)

#     def get(self, request):
#         return JsonResponse({'error': 'Invalid request method'}, status=405)

from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import requests
import datetime
import json
from django.template.defaulttags import register



def summoner_profile(request):
    return render(request, 'index.html')


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

class RiotMatchesView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)

            summoner_name = data.get('summoner_name')
            region = data.get('region', 'NA1').upper()
            language = data.get('language', 'en_US')
            api_key = data.get('api')

            if not summoner_name or not region:
                return JsonResponse({'error': 'Summoner name and region are required'}, status=400)

            headers = {'X-Riot-Token': api_key}

            account_url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner_name}/{region}'
            account_response = requests.get(account_url, headers=headers)
            account_response.raise_for_status()
            account_data = account_response.json()
            puuid = account_data.get('puuid')

            if not puuid:
                return JsonResponse({'error': 'PUUID not found'}, status=404)

            match_ids_url = f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=1'
            match_ids_response = requests.get(match_ids_url, headers=headers)
            match_ids_response.raise_for_status()
            match_ids = match_ids_response.json()

            if not match_ids:
                return JsonResponse({'error': 'No matches found'}, status=404)

            match_url = f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_ids[0]}'
            match_response = requests.get(match_url, headers=headers)
            match_response.raise_for_status()
            match_data = match_response.json()

            match_timestamp = match_data['info']['gameCreation'] / 1000
            match_datetime = datetime.datetime.utcfromtimestamp(match_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')
            game_duration_minutes = match_data['info']['gameDuration'] / 60

            team_totals = {
                100: {'total_gold': 0, 'total_damage': 0},
                200: {'total_gold': 0, 'total_damage': 0}
            }

            for participant in match_data['info']['participants']:
                team_id = participant['teamId']
                team_totals[team_id]['total_gold'] += participant['goldEarned']
                team_totals[team_id]['total_damage'] += participant['totalDamageDealtToChampions']

            response_data = {
                'summoner_name': summoner_name,
                'region': region,
                'language': language,
                'puuid': puuid,
                'match_id': match_ids[0],
                'match_date': match_datetime,
                'game_duration_minutes': game_duration_minutes,
                'match_data': match_data,
                'team_totals': team_totals
            }

            # Save data to session
            request.session['riot_response_data'] = response_data

            return render(request, 'match_details.html', {'response_data': response_data})

        except requests.exceptions.HTTPError as e:
            error_msg = f"API Error: {str(e)}"
            if e.response.status_code == 403:
                error_msg = "Invalid API Key"
            elif e.response.status_code == 404:
                error_msg = "Summoner not found"
            return JsonResponse({'error': error_msg}, status=e.response.status_code)
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'API request failed: {str(e)}'}, status=500)
        except Exception as e:
            return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)

    def get(self, request):
        # Retrieve the saved POST data
        response_data = request.session.get('riot_response_data')
        if response_data:
            return render(request, 'match_details.html', {'response_data': response_data})
        else:
            return JsonResponse({'error': 'No match data available. Please POST first.'}, status=404)


