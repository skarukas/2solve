"""LetterBoxed solver test

Usage:
  python3 -m unittest letter_boxed_test.py
"""

import unittest
from parameterized import parameterized
from dictionary import Dictionary
import letter_boxed


class LetterBoxedTest(unittest.TestCase):

    def setUp(self):
        self.dictionary = Dictionary.open("word_list.txt")

    @parameterized.expand([
        ["GIYERCPOLAHX", [
            # 11-13-2022 1-solve
            # https://www.reddit.com/r/NYTLetterBoxed/comments/ytvhvh/the_1worder_is_finally_here/
            ("lexicography",)
        ]],
        ["BTLEHYVCOIWJ", [("who", "objectively")]],  # 12-30-2023
        ["SVCAERDMWILY", [  # 12-29-2023
            ("calmed", "driveways"),
        ]],
        ["ATRGUFQINLEC", [("cafeteria", "aqualung")]],  # 12-28-2023
        ["RALIFUTXZNEB", [  # 1-5-2024
            ("fertilize", "exurban"),
        ]],
    ])
    def test_solutions(self, board_letters: str, expected_best_solutions, max_solutions=10):
        board = letter_boxed.LetterBoxedBoard(board_letters)
        game = letter_boxed.LetterBoxedGame(self.dictionary, board)
        best_solutions = []
        for i, solution in enumerate(game.solve()):
            if i == max_solutions:
                break
            best_solutions.append(solution.words)
            if set(expected_best_solutions).issubset(best_solutions):
                break
        for sol in expected_best_solutions:
            self.assertIn(sol, best_solutions)
