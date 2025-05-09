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

def summoner_profile(request):
    return render(request, 'index.html')

@method_decorator(csrf_exempt, name='dispatch')
class RiotMatchesView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)

            summoner_name = data.get('summoner_name')
            region = data.get('region', 'NA1').upper()
            language = data.get('language', 'en_US')
            api_key = data.get('api')
            print(f"API Key:-------------------> {api_key}")

            if not summoner_name or not region:
                return JsonResponse({'error': 'Summoner name and region are required'}, status=400)

            api_key = data.get('api')
            headers = {'X-Riot-Token': api_key}

            account_url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner_name}/{region}'
            account_response = requests.get(account_url, headers=headers)

            if account_response.status_code != 200:
                return JsonResponse({'error': 'Failed to fetch account data'}, status=account_response.status_code)

            puuid = account_response.json().get('puuid')
            if not puuid:
                return JsonResponse({'error': 'PUUID not found'}, status=404)

            match_ids_url = f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids'
            match_ids_response = requests.get(match_ids_url, headers=headers)

            if match_ids_response.status_code != 200:
                return JsonResponse({'error': 'Failed to fetch match IDs'}, status=match_ids_response.status_code)

            match_ids = match_ids_response.json()
            if not match_ids:
                return JsonResponse({'error': 'No matches found'}, status=404)

            # Fetch match details for each match ID
            matches_data = []
            summoner_stats = {
                'total_matches': 0,
                'total_kills': 0,
                'total_deaths': 0,
                'total_assists': 0,
                'total_gold': 0,
                'total_damage': 0,
                'total_cs': 0,
                'wins': 0,
            }

            for match_id in match_ids:
                match_url = f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}'
                try:
                    match_response = fetch_with_retry(match_url, headers)
                    match_data = match_response.json()


                    # Fetch summoner names for participants if not available
                    if 'participantIdentities' in match_data['info']:
                        for identity in match_data['info']['participantIdentities']:
                            participant_id = identity['participantId']
                            summoner_name = identity['player']['summonerName']
                            # Add summoner name to corresponding participant
                            for participant in match_data['info']['participants']:
                                if participant['participantId'] == participant_id:
                                    participant['summonerName'] = summoner_name
                                    break
                    
                    
                    # Ensure match_data has required fields
                    if not match_data.get('info') or not match_data['info'].get('participants'):
                        continue  # Skip malformed matches

                    match_timestamp = match_data['info']['gameCreation'] / 1000
                    match_datetime = datetime.datetime.utcfromtimestamp(match_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')
                    game_duration_minutes = match_data['info']['gameDuration'] / 60

                    team_totals = {
                        100: {'total_gold': 0, 'total_damage': 0},
                        200: {'total_gold': 0, 'total_damage': 0}
                    }
                    for participant in match_data['info']['participants']:
                        team_id = participant.get('teamId', 0)
                        if team_id not in team_totals:
                            team_totals[team_id] = {'total_gold': 0, 'total_damage': 0}
                        team_totals[team_id]['total_gold'] += participant.get('goldEarned', 0)
                        team_totals[team_id]['total_damage'] += participant.get('totalDamageDealtToChampions', 0)

                        # Aggregate summoner stats
                        if participant.get('puuid') == puuid:
                            summoner_stats['total_matches'] += 1
                            summoner_stats['total_kills'] += participant.get('kills', 0)
                            summoner_stats['total_deaths'] += participant.get('deaths', 0)
                            summoner_stats['total_assists'] += participant.get('assists', 0)
                            summoner_stats['total_gold'] += participant.get('goldEarned', 0)
                            summoner_stats['total_damage'] += participant.get('totalDamageDealtToChampions', 0)
                            summoner_stats['total_cs'] += participant.get('totalMinionsKilled', 0) + participant.get('neutralMinionsKilled', 0)
                            summoner_stats['wins'] += 1 if participant.get('win', False) else 0

                    matches_data.append({
                        'match_id': match_id,
                        'match_date': match_datetime,
                        'game_duration_minutes': game_duration_minutes,
                        'match_data': match_data,
                        'team_totals': team_totals
                    })

                except requests.exceptions.RequestException as e:
                    print(f"Failed to fetch match {match_id}: {str(e)}")
                    continue  # Skip failed matches

            if not matches_data:
                return JsonResponse({'error': 'No valid match data retrieved'}, status=404)

            # Calculate average summoner stats
            if summoner_stats['total_matches'] > 0:
                summoner_stats['avg_kda'] = (
                    f"{summoner_stats['total_kills'] / summoner_stats['total_matches']:.1f}/"
                    f"{summoner_stats['total_deaths'] / summoner_stats['total_matches']:.1f}/"
                    f"{summoner_stats['total_assists'] / summoner_stats['total_matches']:.1f}"
                )
                summoner_stats['avg_gold'] = summoner_stats['total_gold'] / summoner_stats['total_matches']
                summoner_stats['avg_damage'] = summoner_stats['total_damage'] / summoner_stats['total_matches']
                summoner_stats['avg_cs'] = summoner_stats['total_cs'] / summoner_stats['total_matches']
                summoner_stats['win_rate'] = (summoner_stats['wins'] / summoner_stats['total_matches']) * 100
            else:
                summoner_stats['avg_kda'] = 'N/A'
                summoner_stats['avg_gold'] = 0
                summoner_stats['avg_damage'] = 0
                summoner_stats['avg_cs'] = 0
                summoner_stats['win_rate'] = 0

            response_data = {
                'summoner_name': summoner_name,
                'region': region,
                'language': language,
                'puuid': puuid,
                'match_id': match_ids[0],
                'match_date': match_datetime,
                'match_data': match_data,
                'match_data_json': match_data_json,
                'summarized_match_info': summarized_match_info  # Add summarized data
            }

            return render(request, 'match_details.html', {'response_data': response_data})

        except requests.RequestException as e:
            return JsonResponse({'error': f'API request failed: {str(e)}'}, status=500)
        except Exception as e:
            return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)

    def get(self, request):
        return JsonResponse({'error': 'Invalid request method'}, status=405)