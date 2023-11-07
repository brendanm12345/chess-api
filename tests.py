import unittest
from unittest.mock import patch, Mock
from chess import fetch_top_classical_players, fetch_last_30_day_rating_for_player

class TestChessAPI(unittest.TestCase):

    def test_fetch_top_classical_players(self):
        # Mock response data
        fake_response = {
            'users': [
                {'username': 'player1', 'rating': 2500},
                {'username': 'player2', 'rating': 2400},
                {'username': 'player3', 'rating': 2300},
                {'username': 'player4', 'rating': 2200},
                {'username': 'player5', 'rating': 2100},
                {'username': 'player6', 'rating': 2000},
                {'username': 'player7', 'rating': 1900},
                {'username': 'player8', 'rating': 1800},
                {'username': 'player9', 'rating': 1700},
                {'username': 'player10', 'rating': 1600},
                {'username': 'player11', 'rating': 1500},
                {'username': 'player12', 'rating': 1400},
                {'username': 'player13', 'rating': 1300},
                {'username': 'player14', 'rating': 1200},
                {'username': 'player15', 'rating': 1100},
            ]
        }
        with patch('chess.requests.get') as mock_get:
            mock_get.return_value = Mock(ok=True)
            mock_get.return_value.json.return_value = fake_response

            players = fetch_top_classical_players(2)

            mock_get.assert_called_with(
                'https://lichess.org/api/player/top/2/classical')
            self.assertEqual(len(players), 2)
            self.assertEqual(players[0]['username'], 'player1')
            self.assertEqual(players[1]['username'], 'player2')

    def test_fetch_last_30_day_rating_for_player(self):
        fake_rating_response = [{
            'name': 'Classical',
            'points': [
                [2023, 9, 1, 2400],
                [2023, 9, 2, 2410],
                [2023, 9, 3, 2420],
                [2023, 9, 4, 2430],
                [2023, 9, 8, 2470],
                [2023, 9, 9, 2480],
                [2023, 9, 12, 2510],
                [2023, 9, 13, 2520],
                [2023, 9, 14, 2524],
                [2023, 9, 16, 2520],
                [2023, 9, 20, 2520],
                [2023, 9, 21, 2300],
                [2023, 9, 22, 2400],
                [2023, 9, 24, 2510],
                [2023, 9, 25, 2520],
                [2023, 9, 26, 2519],
                [2023, 9, 27, 2522],
                [2023, 9, 29, 2518],
                [2023, 10, 3, 2520],
            ]
        }]
        with patch('chess.requests.get') as mock_get:
            mock_get.return_value = Mock(ok=True)
            mock_get.return_value.json.return_value = fake_rating_response

            ratings = fetch_last_30_day_rating_for_player('mockuser')

            self.assertIsInstance(ratings, dict)
            print("Data received:", ratings)
            self.assertEqual(ratings['today-0'], 2520)
            self.assertEqual(ratings['today-1'], 2520)
            self.assertEqual(ratings['today-3'], 2518)
            self.assertEqual(ratings['today-4'], 2518)
            self.assertEqual(ratings['today-29'], 2430)


if __name__ == '__main__':
    unittest.main()
