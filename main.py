import requests
import messages
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from prepare_data import extract_input, get_team_id, generate_response
import telegram
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from config import *
from models import Language, Status


def estimate_match_score(home_team_id=85, away_team_id=94):
    """Very initial (dummy) match score estimation -- not being used"""

    team_url = f"{api_url}/fixtures/headtohead"
    headers = {"X-RapidAPI-Key": rapid_api_token, "X-RapidAPI-Host": rapid_api_host}
    querystring = {
        "h2h": "85-94",
    }
    response = requests.get(team_url, headers=headers, params=querystring)
    data = response.json()

    df = pd.json_normalize(data["response"])

    # Filter the data for the specified home and away teams
    filtered_data = df[
        (
            ((df["teams.home.id"] == home_team_id) & (df["teams.away.id"] == away_team_id))
            | ((df["teams.home.id"] == away_team_id) & (df["teams.away.id"] == home_team_id))
        )
        & (df["fixture.status.short"] != "CANC")
    ]

    filtered_data = filtered_data.fillna(0)

    X = filtered_data[["goals.home", "goals.away"]].values.tolist()
    y = (filtered_data["goals.home"] - filtered_data["goals.away"]).values.tolist()

    # Train the linear regression model
    model = LinearRegression()
    model.fit(X, y)

    # Predict the score for the next match
    next_match_home_goals = 2  # Example: Set the expected home goals for the next match
    next_match_away_goals = 1  # Example: Set the expected away goals for the next match

    predicted_score_difference = model.predict([[next_match_home_goals, next_match_away_goals]])
    predicted_home_goals = (predicted_score_difference + next_match_home_goals) / 2
    predicted_away_goals = next_match_home_goals - predicted_home_goals

    # Plot the data and the linear regression line
    plt.scatter(X, y, color="blue", label="Data")
    plt.plot(predicted_home_goals, predicted_score_difference, color="red", label="Linear Regression")
    plt.xlabel("X")
    plt.ylabel("y")
    plt.title("Linear Regression")
    plt.legend()
    plt.show()

    return {
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "predicted_home_goals": predicted_home_goals,
        "predicted_away_goals": predicted_away_goals,
    }


def start(update, context):
    message = (
        "Welcome! Xoş gəldiniz! Добро пожаловать!\n\n"
        "Please, select a language\n"
        "Zəhmət olmasa, bir dil seçin\n"
        "Пожалуйста, выберите язык\n"
    )

    reply_keyboard = [["Azərbaycan dili"], ["Русский язык"], ["English"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, reply_markup=markup)

    return Status.LANGUAGE


def process_language_selection(update, context):
    """Set language based on selection"""

    message = update.message.text
    language = message.lower()

    if language == "english":
        context.user_data["language"] = Language.EN
    elif language == "azərbaycan dili":
        context.user_data["language"] = Language.AZ
    elif language == "русский язык":
        context.user_data["language"] = Language.RU
    else:
        response = "Invalid language selection. Please try again."
        context.bot.send_message(chat_id=update.effective_chat.id, text=response)
        context.user_data["language"] = Language.EN

        return Status.LANGUAGE

    response = messages.you_selected_lang[context.user_data["language"]]
    context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=messages.enter_details[context.user_data["language"]]
    )

    return Status.INPUT


def process_input(update, context):
    """Main function to call functions for getting data, processing, estimation and response"""

    language = context.user_data.get("language")
    message = update.message.text

    # Extract team names and date from the input message
    team_names, date = extract_input(message)

    if team_names is None or date is None:
        response = messages.invalid_input_format[language]
        context.bot.send_message(chat_id=update.effective_chat.id, text=response)
        return

    # Validate the game using the API-Football service
    fixture = validate_game(team_names, date)

    if fixture is None:
        response = messages.no_such_game[language]
        context.bot.send_message(chat_id=update.effective_chat.id, text=response)
        return Status.INPUT
    else:
        # Perform estimation based on previous H2H games
        estimation = perform_estimation(team_names, date)
        prediction_from_api = get_predictions_from_api(fixture)
        # Generate response with estimation results adn prediction from API
        response = generate_response(fixture, estimation, prediction_from_api, language)

    context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=messages.enter_details[context.user_data["language"]]
    )


def validate_game(team_names, date):
    """check if such game exists"""

    url = f"{api_url}/fixtures/headtohead"
    headers = {"X-RapidAPI-Key": rapid_api_token, "X-RapidAPI-Host": rapid_api_host}

    team1_id = get_team_id(team_names[0])
    team2_id = get_team_id(team_names[1])

    if team1_id and team2_id:
        querystring = {"h2h": f"{team1_id}-{team2_id}", "date": date, "season": "2022"}
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()

        if "response" in data and len(data["response"]) > 0:
            # Check if team 2 ID is present in the fixtures
            fixtures = data["response"]
            if len(fixtures) > 0:
                return fixtures[0]

    return None


def perform_estimation(team_names, date):
    """Dummy data"""

    estimation = {
        "score": "2-1",
        "penalties": 3,
        "corners": 8,
        "faults": 12,
        "red_cards": 1,
        "yellow_cards": 4,
        "injuries": ["Player1", "Player2"],
    }

    return estimation


def get_predictions_from_api(fixture):
    url = f"{api_url}/predictions"
    headers = {"X-RapidAPI-Key": rapid_api_token, "X-RapidAPI-Host": rapid_api_host}

    querystring = {"fixture": fixture["fixture"]["id"]}

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()

    if "response" in data:
        return data["response"][0]

    return None


def cancel(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Input process cancelled.")
    return ConversationHandler.END


if __name__ == "__main__":
    bot = telegram.Bot(token=telegram_bot_token)
    updater = Updater(token=telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            Status.LANGUAGE: [MessageHandler(Filters.text & ~Filters.command, process_language_selection)],
            Status.INPUT: [MessageHandler(Filters.text & ~Filters.command, process_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
