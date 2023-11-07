# Author: Brendan McLaughlin
# Date: 11/7/2023
# For: SWE Intern Take-Home

import requests
from requests.exceptions import RequestException
import csv
from datetime import datetime, timedelta, date
from concurrent.futures import ThreadPoolExecutor, as_completed

STYLE = 'classical'
BASE_URL = "https://lichess.org/api"
DATE_FORMAT = '%Y-%m-%d'
DAYS_BACK = 31

today = datetime.today().date()
dates = [(today - timedelta(days=i)).strftime(DATE_FORMAT) for i in range(DAYS_BACK)][::-1]


def fetch_top_classical_players(n=50) -> list:
    """
    Fetches the top N classical chess players
    """
    players = []
    try:
        resp = requests.get(f'{BASE_URL}/player/top/{n}/{STYLE}')
        resp.raise_for_status()
        data = resp.json()

        if 'users' in data:
            players = data['users'][:n]
        else:
            print("Error: The response JSON does not contain the 'users' key.")

    except RequestException as e:
        print(f"An error occurred while making the request: {e}")
    except ValueError:
        print("Error: Failed to parse JSON response.")
    
    return players

# Warmup: List the top 50 classical chess players. Just print their usernames.
def print_top_50_classical_players() -> None:
    players = fetch_top_classical_players()
    for player in players:
        print(player['username'])
    

def fetch_last_30_day_rating_for_player(username) -> dict:
    """
    Fetches the rating history for the top classical chess player for the last 30 days 
    and returns a dict in format: {username: {today-29: 990, today-28: 991, etc}}
    """
    try:
        resp = requests.get(f'{BASE_URL}/user/{username}/rating-history')
        resp.raise_for_status()
        data = resp.json()

        # Filter the rating history by desired chess style, in this case Classical
        classical_history = next((category for category in data if category['name'] == STYLE.capitalize()), None)
        if not classical_history:
            return {}
        
        # Create a mapping of date to rating
        classical_ratings = {datetime(year, month + 1, day).date(): rating for year, month, day, rating in classical_history['points']}

        # Find the last known rating before the 30-day period
        last_known_rating = None
        for date in sorted(classical_ratings.keys(), reverse=True):
            if date < (today - timedelta(days=30)):
                last_known_rating = classical_ratings[date]
                break

        # Initialize the last 30 days with -1 to indicate missing rating
        rating_by_day = {today - timedelta(days=i): -1 for i in range(DAYS_BACK)}

        # Fill the dictionary with the available ratings
        for rating_date, rating in classical_ratings.items():
            if rating_date in rating_by_day:
                rating_by_day[rating_date] = rating
        
        # Loop back the other way to fill in the -1s with the last known rating
        for date in sorted(rating_by_day.keys()):
            if rating_by_day[date] == -1:
                rating_by_day[date] = last_known_rating
            else:
                last_known_rating = rating_by_day[date]
        
        # Convert date keys back to 'today-x' format
        rating_by_day_formatted = {f"today-{(today - date).days}": rating if rating is not None else "No rating found" 
                                   for date, rating in rating_by_day.items()}

        return rating_by_day_formatted
        
    except RequestException as e:
        print(f"An error occurred while making the request: {e}")
    except ValueError:
        print("Error: Failed to parse JSON response.")

    
# PART 2: Print the rating history for the top chess player in classical chess for the last 30 calendar days.
# This can be in the format: username, {today-29: 990, today-28: 991, etc}
def print_last_30_day_rating_for_top_player() -> None:
    # Get top player
    players = fetch_top_classical_players(1)
    if not players:
        print("No players found.")
        return
    
    username = players[0]['username']

    # Get rating history for top player
    rating_by_day = fetch_last_30_day_rating_for_player(username)
    print(f"{username}: {rating_by_day}")


# PART 3: Create a CSV that shows the rating history for each of these 50 players, for the last 30 days.
# The CSV should have 51 rows (1 header, 50 players).
# The CSV should be in the same order of the leaderboard.
def generate_rating_csv_for_top_50_classical_players() -> None:
    players = fetch_top_classical_players()
    if not players:
        print("No players found.")
        return

    # Thread pool to fetch data concurrently for speed
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Start the load operations and mark each future with its URL
        future_to_username = {executor.submit(fetch_last_30_day_rating_for_player, player['username']): player['username'] for player in players}
        ratings = {}
        for future in as_completed(future_to_username):
            username = future_to_username[future]
            try:
                player_ratings_raw = future.result()
                player_ratings = { (today - timedelta(days=int(key.split('-')[1]))).strftime('%Y-%m-%d'): value for key, value in player_ratings_raw.items() }
                ratings[username] = player_ratings
            except Exception as e:
                print(f"{username} generated an exception: {e}")
                ratings[username] = {}

    # Extract latest ratings for sorting
    latest_ratings = {
        username: player_ratings.get(datetime.today().strftime('%Y-%m-%d'), 0)
        for username, player_ratings in ratings.items()
    }
    # Sort by latest rating value in descending order
    sorted_ratings = sorted(latest_ratings, key=latest_ratings.get, reverse=True)


    # Write CSV
    with open('ratings.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write the header
        writer.writerow(['username'] + dates)
        # Write the player ratings
        for username in sorted_ratings:
            # Prepare a list of ratings for each date
            player_ratings = [ratings[username].get(date, '') for date in dates]
            writer.writerow([username] + player_ratings)

    
def main() -> None:
    print('\n Printing top 50 classical players: \n')
    print_top_50_classical_players()
    print('\n Printing last 30 day rating for top player: \n')
    print_last_30_day_rating_for_top_player()
    print('\n Generating CSV for top 50 classical players: \n')
    generate_rating_csv_for_top_50_classical_players()

main()