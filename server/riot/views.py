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
import csv
import time
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import requests
import datetime
import json
from django.template.defaulttags import register
from django.urls import reverse

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

def summoner_profile(request):
    return render(request, 'index.html')

def fetch_with_retry(url, headers, retries=3, backoff=1):
    """Helper function to retry API calls on rate limit errors."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                time.sleep(backoff * (2 ** attempt))
                continue
            raise
    raise Exception("Max retries reached")

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
            match_count = data.get('match_count', 10)  # Default to 10 matches

            if not summoner_name or not region:
                return JsonResponse({'error': 'Summoner name and region are required'}, status=400)

            api_key = data.get('api')
            headers = {'X-Riot-Token': api_key}

            # Fetch account data
            account_url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner_name}/{region}'
            account_response = fetch_with_retry(account_url, headers)
            account_data = account_response.json()
            puuid = account_data.get('puuid')

            if not puuid:
                return JsonResponse({'error': 'PUUID not found'}, status=404)

            # Fetch multiple match IDs
            match_ids_url = f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={match_count}'
            match_ids_response = fetch_with_retry(match_ids_url, headers)
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
                'matches': matches_data,
                'summoner_stats': summoner_stats
            }

            # Save data to session
            request.session['riot_response_data'] = response_data
            return redirect(reverse('match_details'))

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

def match_details(request):
    response_data = request.session.get('riot_response_data')
    if response_data:
        return render(request, 'match_details.html', {'response_data': response_data})
    else:
        return JsonResponse({'error': 'No match data available. Please POST first.'}, status=404)

def download_match_csv(request):
    if request.method == 'POST':
        response_data = request.session.get('riot_response_data')
        if not response_data:
            return JsonResponse({'error': 'No match data available.'}, status=404)

        summoner_only = request.POST.get('summoner_only') == 'true'
        selected_match_id = request.POST.get('match_id')
        matches = response_data['matches']
        if selected_match_id:
            matches = [m for m in matches if m['match_id'] == selected_match_id]
            if not matches:
                return JsonResponse({'error': 'Selected match not found.'}, status=404)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="matches_{response_data["summoner_name"]}.csv"'

        writer = csv.writer(response)
        headers = [
            'Match ID', 'Match Date', 'Summoner', 'Champion', 'Position', 'Level', 'KDA', 'CS', 'Gold',
            'Damage to Champions', 'Physical Damage', 'Magic Damage', 'True Damage', 'Damage Taken',
            'Healing Done', 'Shielding Done', 'Vision Score', 'Wards Placed', 'Wards Killed',
            'CC Score', 'Dragon Kills', 'Baron Kills', 'Turret Kills', 'Win', 'Summoner Spells', 'Runes', 'Team ID', 'Items'
        ]
        writer.writerow(headers)

        for match in matches:
            for participant in match['match_data']['info']['participants']:
                if summoner_only and participant.get('puuid') != response_data['puuid']:
                    continue  # Skip non-summoner participants

                items = [
                    f"Item{i}: {participant.get(f'item{i}', 0)}"
                    for i in range(7) if participant.get(f'item{i}', 0) != 0
                ]
                items_str = '; '.join(items) if items else 'None'

                summoner_spells = f"{participant.get('summoner1Id', 'N/A')} & {participant.get('summoner2Id', 'N/A')}"

                perks = participant.get('perks', {}).get('styles', [])
                runes = []
                for style in perks:
                    for selection in style.get('selections', []):
                        runes.append(str(selection.get('perk', '')))
                runes_str = ', '.join(runes) if runes else 'None'

                row = [
                    match['match_id'],
                    match['match_date'],
                    response_data['summoner_name'] + ' (YOU)' if participant.get('puuid') == response_data.get('puuid') else participant.get('summonerName', 'Unknown'),
                    participant['championName'],
                    participant['teamPosition'],
                    participant['champLevel'],
                    f"{participant['kills']}/{participant['deaths']}/{participant['assists']}",
                    participant['totalMinionsKilled'] + participant['neutralMinionsKilled'],
                    participant['goldEarned'],
                    participant['totalDamageDealtToChampions'],
                    participant['physicalDamageDealtToChampions'],
                    participant['magicDamageDealtToChampions'],
                    participant['trueDamageDealtToChampions'],
                    participant['totalDamageTaken'],
                    participant.get('totalHeal', 0),
                    participant.get('totalShieldingOnTeammates', 0),
                    participant['visionScore'],
                    participant.get('wardsPlaced', 0),
                    participant.get('wardsKilled', 0),
                    participant.get('timeCCingOthers', 0),
                    participant.get('dragonKills', 0),
                    participant.get('baronKills', 0),
                    participant.get('turretKills', 0),
                    'Yes' if participant.get('win', False) else 'No',
                    summoner_spells,
                    runes_str,
                    participant['teamId'],
                    items_str
                ]
                writer.writerow(row)

        return response
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    
    