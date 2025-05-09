import openpyxl
from io import BytesIO

def generate_excel_file(response_data, summoner_only, selected_match_id=None):
    """Helper function to generate an Excel file from match data."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Match Data"

    # Define headers
    headers = [
        'Match ID', 'Match Date', 'Summoner', 'Champion', 'Position', 'Level', 'KDA', 'CS', 'Gold',
        'Damage to Champions', 'Physical Damage', 'Magic Damage', 'True Damage', 'Damage Taken',
        'Healing Done', 'Shielding Done', 'Vision Score', 'Wards Placed', 'Wards Killed',
        'CC Score', 'Dragon Kills', 'Baron Kills', 'Turret Kills', 'Win', 'Summoner Spells', 'Runes', 'Team ID', 'Items'
    ]
    sheet.append(headers)

    # Filter matches if a specific match_id is provided
    matches = response_data['matches']
    if selected_match_id:
        matches = [m for m in matches if m['match_id'] == selected_match_id]
        if not matches:
            return None  # Return None if no matches found

    # Populate data
    for match in matches:
        for participant in match['match_data']['info']['participants']:
            if summoner_only and participant.get('puuid') != response_data['puuid']:
                continue

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
            sheet.append(row)

    # Save workbook to a BytesIO buffer
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer