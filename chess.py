import requests
from requests.exceptions import RequestException
import csv
from datetime import datetime, timedelta, date
from concurrent.futures import ThreadPoolExecutor, as_completed

STYLE = 'classical'

def fetch_top_classical_players(n=50) -> list:
    """
    Fetches the top N classical chess players
    """
    players = []
    try:
        resp = requests.get(f'https://lichess.org/api/player/top/{n}/{STYLE}')
        resp.raise_for_status()
        data = resp.json()

        if 'users' in data:
            players = data['users'][:n]
        else:
            print("Error: The response JSON does not contain the 'users' key.")

    except requests.RequestException as e:
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
        resp = requests.get(f'https://lichess.org/api/user/{username}/rating-history')
        resp.raise_for_status()
        data = resp.json()
        print('SEARCH: ', data)

        # Filter the rating history by desired chess style, in this case Classical
        classical_history = next((category for category in data if category['name'] == STYLE.capitalize()), None)
        if not classical_history:
            return {}
        
        # this mihgt need to be removed because the data is already sort in ascedning order by date
        classical_history['points'].sort(key=lambda x: date(int(x[0]), int(x[1] + 1), int(x[2])))
        
        today = datetime.today()
        rating_by_day = {}
        last_known_rating = None

        # Iterate through the last 30 days and find the last known rating for each day
        for days_ago in range(29, -1, -1):
            check_date = today - timedelta(days=days_ago)

            for entry in classical_history['points']:
                rating_date = datetime(entry[0], entry[1] + 1, entry[2])
                if rating_date <= check_date:
                    last_known_rating = entry[3]
            
            # EDGE CASE: If last_known_rating is still None, find the nearest last known time
            if last_known_rating is None:
                for entry in reversed(classical_history['points']):
                    rating_date = datetime(entry[0], entry[1] + 1, entry[2])
                    if rating_date < check_date:
                        last_known_rating = entry[3]
                        break

            rating_by_day[f"today-{days_ago}"] = last_known_rating if last_known_rating is not None else "No rating found"

        return rating_by_day
    except requests.RequestException as e:
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

# The first column in the csv should be the username of the player.
# Columns afterward should be the player's rating on the specified date.
# A CSV could look like this:
# username,2022-01-01,2022-01-02,2022-01-03,.....,2022-01-31
# bob,1231,1158,1250,...,1290
# notagm,900,900,900,...,900

def generate_rating_csv_for_top_50_classical_players() -> None:
    players = fetch_top_classical_players()
    if not players:
        print("No players found.")
        return

    # Prepare dates for the header
    dates = [(datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)][::-1]

    # Use a thread pool to fetch data concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Start the load operations and mark each future with its URL
        future_to_username = {executor.submit(fetch_last_30_day_rating_for_player, player['username']): player['username'] for player in players}
        ratings = {}
        for future in as_completed(future_to_username):
            username = future_to_username[future]
            try:
                player_ratings_raw = future.result()
                player_ratings = { (datetime.today() - timedelta(days=int(key.split('-')[1]))).strftime('%Y-%m-%d'): value for key, value in player_ratings_raw.items() }
                ratings[username] = player_ratings
            except Exception as e:
                print(f"{username} generated an exception: {e}")
                ratings[username] = {}

    # Write CSV
    with open('ratings.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write the header
        writer.writerow(['username'] + dates)
        # Write the player ratings
        for username in ratings:
            # Prepare a list of ratings for each date
            player_ratings = [ratings[username].get(date, '') for date in dates]
            writer.writerow([username] + player_ratings)
    
def main() -> None:
    print_top_50_classical_players()
    print_last_30_day_rating_for_top_player()
    # generate_rating_csv_for_top_50_classical_players()

main()