from helper import messages


def extract_input(message):
    parts = message.split(",")

    if len(parts) != 3:
        return None, None

    team1 = parts[0].strip()
    team2 = parts[1].strip()
    date = parts[2].strip()

    return (team1, team2), date


def generate_response(fixture, estimation, predictions, language):
    if fixture is None:
        return messages.no_such_game[language]

    home_team = fixture["teams"]["home"]["name"]
    away_team = fixture["teams"]["away"]["name"]
    date = fixture["fixture"]["date"]
    venue = fixture["fixture"]["venue"]["name"]
    referee = fixture["fixture"]["referee"]
    status = fixture["fixture"]["status"]["long"]
    goals_home = fixture["goals"]["home"]
    goals_away = fixture["goals"]["away"]
    home_win_percent = predictions["predictions"]["percent"]["home"]
    away_win_percent = predictions["predictions"]["percent"]["away"]
    draw_percent = predictions["predictions"]["percent"]["draw"]

    response = f"⚽⚽⚽{messages.match_details[language]}⚽⚽⚽\n"
    response += f"{messages.date[language]}: {date}\n"
    response += f"{messages.venue[language]}: {venue}\n"
    response += f"{messages.referee[language]}: {referee}\n"
    response += f"{messages.status[language]}: {status}\n\n"
    response += f"{home_team} vs {away_team}\n"
    response += f"{messages.score[language]}: {goals_home} - {goals_away}\n"

    response += f"\n💯💯💯{messages.predictions[language]}💯💯💯 (Dev. Purpose)\n"
    response += f"{predictions['teams']['home']['name']} {messages.win[language]}: {home_win_percent}\n"
    response += f"{predictions['teams']['away']['name']} {messages.win[language]}: {away_win_percent}\n"
    response += f"{messages.draw[language]}: {draw_percent}\n"
    response += f"{predictions['predictions']['winner']['comment']}: {predictions['predictions']['winner']['name']}\n"

    try:
        if float(predictions["predictions"]["under_over"]) < 0:
            response += f"Overall {int(float(predictions['predictions']['under_over']))} goals or less\n"
        else:
            response += f"Overall {int(float(predictions['predictions']['under_over']) + 1)} goals or more\n"
    except TypeError:
        print("No under_over data")

    response += f"{predictions['teams']['home']['name']} goals: "
    if float(predictions["predictions"]["goals"]["home"]) < 0:
        response += f"{abs(int(float(predictions['predictions']['goals']['home'])))} goals or less\n"
    else:
        response += f"Overall {int(float(predictions['predictions']['goals']['home']) + 1)} goals or more\n"
    response += f"{predictions['teams']['away']['name']} goals: "
    if float(predictions["predictions"]["goals"]["away"]) < 0:
        response += f"{abs(int(float(predictions['predictions']['goals']['away'])))} goals or less\n"
    else:
        response += f"Overall {int(float(predictions['predictions']['goals']['away']) + 1)} goals or more\n"

    if estimation and fixture["fixture"]["status"]["short"] == "NS":
        response += f"\n💯💯💯{messages.estimation[language]}💯💯💯 (fake data)\n"
        response += f"{messages.estimated[language]} {messages.score[language]}: {estimation['score']}\n"
        response += f"{messages.estimated[language]} {messages.penalties[language]}: {estimation['penalties']}\n"
        response += f"{messages.estimated[language]} {messages.corners[language]}: {estimation['corners']}\n"
        response += f"{messages.estimated[language]} {messages.faults[language]}: {estimation['faults']}\n"
        response += f"{messages.estimated[language]} {messages.red_cards[language]}: {estimation['red_cards']}\n"
        response += f"{messages.estimated[language]} {messages.yellow_cards[language]}: {estimation['yellow_cards']}\n"
        response += f"{messages.estimated[language]} {messages.injuries[language]}: {estimation['injuries']}\n"

    else:
        response += f"\n\n{messages.finished_match[language]}\n"

    return response
