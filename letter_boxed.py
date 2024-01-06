from __future__ import annotations

from dictionary import Dictionary
from typing import Iterator, TypeAlias, Any
import dataclasses
import random
import functools

from queue import PriorityQueue

Comparable: TypeAlias = Any


def print_it(fn, show_args=False):
    def _inner(*args, **kwargs):
        res = fn(*args, **kwargs)
        print(fn.__name__)
        if show_args:
            print("ARGS:", args)
            print("KWARGS:", kwargs)
        print(res)
        return res
    return _inner


@functools.total_ordering
@dataclasses.dataclass
class LetterBoxedState:
    subtrie: Dictionary.Trie
    game: LetterBoxedGame
    # Full list of letters (not repeating edge letters)
    letters: tuple[str] = tuple()
    words: tuple[str] = tuple()
    word_in_progress: str = ""
    # Indexed clockwise from top left, no repeat.
    edge_index_sequence: tuple[int] = tuple()

    def finish_last_word(self) -> 'LetterBoxedState':
        new_words = (*self.words, self.word_in_progress)
        connect_letter = self.letters[-1]
        new_word_in_progress = connect_letter
        return LetterBoxedState(
            subtrie=self.game.dictionary.prefix_tree.get(connect_letter, {}),
            game=self.game,
            letters=self.letters,
            words=new_words,
            word_in_progress=new_word_in_progress,
            edge_index_sequence=self.edge_index_sequence,
        )

    def place_letter(self, letter: str, edge_index: int) -> 'LetterBoxedState':
        new_index_sequence = (*self.edge_index_sequence, edge_index)
        new_letters = (*self.letters, letter)
        new_word_in_progress = self.word_in_progress + letter
        return LetterBoxedState(
            subtrie=self.subtrie[letter],
            game=self.game,
            letters=new_letters,
            words=self.words,
            word_in_progress=new_word_in_progress,
            edge_index_sequence=new_index_sequence,
        )

    def is_valid_next_edge_index(self, edge_index: int) -> bool:
        return not (
            self.edge_index_sequence
            and edge_index == self.edge_index_sequence[-1]
        )

    def can_place_letter(self, letter: str, edge_index: int) -> bool:
        return letter in self.subtrie \
            and self.is_valid_next_edge_index(edge_index)

    def can_finish_word(self) -> bool:
        return len(self.word_in_progress) >= self.game.min_word_length \
            and Dictionary.END_TOKEN in self.subtrie

    def num_unused_dots(self) -> int:
        # TODO: len(set(self.letters)) only works if each letter only appears once. Keep track of the "indices" too.
        return self.game.board.num_dots - len(set(self.letters))

    # @print_it
    def is_final_state(self) -> int:
        return len(self.word_in_progress) < 2 \
            and not self.num_unused_dots()

    def priority(self) -> Comparable:
        """Returns a comparable value representing the state's priority (lower is better)"""
        return (len(self.words), self.num_unused_dots(), len(self.letters))

    def __lt__(self, other: LetterBoxedState) -> bool:
        return self.priority() < other.priority()

    def __repr__(self) -> str:
        return f"""LetterBoxedState(
  {self.words=}
  {self.edge_index_sequence=}
  {self.letters=}
  {self.word_in_progress=}
)"""

    def __hash__(self) -> int:
        key = (self.edge_index_sequence, self.letters, self.word_in_progress)
        return hash(key)


class LetterBoxedBoard:
    def __init__(self, letters: str, num_sides: int = 4):
        """Letters should be a a string reading clockwise from the top left corner around the box. It's expected that letters is divisible by num_sides."""
        self.num_sides = num_sides
        self.num_dots = len(letters)
        dots_per_edge = self.num_dots // num_sides
        self.edge_letters = [
            letters[side_idx*dots_per_edge:(side_idx+1)*dots_per_edge].lower()
            for side_idx in range(num_sides)
        ]

    def all_letters(self) -> list[str]:
        return [l for edge in self.edge_letters for l in edge]


@dataclasses.dataclass
class LetterBoxedGame:
    dictionary: Dictionary
    board: LetterBoxedBoard
    min_word_length: int = 3

    def __init__(self, dictionary: Dictionary, board: LetterBoxedBoard, min_word_length: int = 3):
        self.board = board
        self.min_word_length = min_word_length
        old_len = len(dictionary)
        self.dictionary = dictionary
        self.dictionary = self.dictionary.filter(self.try_playing_on_board)
        print(
            f"Scaled dictionary from {old_len} to {len(self.dictionary)} entries.")

    def get_child_letter_states(self, state: LetterBoxedState) -> list[LetterBoxedState]:
        next_states = []
        for edge_index, edge_letters in enumerate(self.board.edge_letters):
            if state.is_valid_next_edge_index(edge_index):
                next_states.extend([
                    state.place_letter(letter, edge_index)
                    for letter in edge_letters
                    if state.can_place_letter(letter, edge_index)
                ])
        if state.can_finish_word():
            next_states.append(state.finish_last_word())
        random.shuffle(next_states)
        return next_states

    def get_child_word_states(self, state: LetterBoxedState) -> list[LetterBoxedState]:
        next_states = []
        for word in self.dictionary._word_set:
            if state.word_in_progress in ("", word[0]):
                next_state = self.try_playing_on_board(word, state)
                if next_state is not None:
                    next_states.append(next_state)
        random.shuffle(next_states)
        return next_states

    def try_playing_on_board(self, s: str, start_state: LetterBoxedState | None = None) -> LetterBoxedState | None:
        """Linear version that assumes each letter appears only once."""
        if start_state is None:
            state = LetterBoxedState(self.dictionary.prefix_tree, game=self)
        else:
            state = start_state
        if state.words:
            s = s[1:]

        for l in s:
            valid_edge_idx = [
                edge_index
                for edge_index, edge_letters in enumerate(self.board.edge_letters)
                if l in edge_letters
            ]
            if valid_edge_idx and state.can_place_letter(l, valid_edge_idx[0]):
                state = state.place_letter(l, valid_edge_idx[0])
            else:
                return None
        return state.finish_last_word() if state.can_finish_word() else None

    def can_be_played_in_game_dfs(self, s: str) -> bool:
        """Checks if a path through the board exists for the word.

        This is only DFS for the case that a letter appears twice, so we have to explore either possibility.
        """
        if len(s) < self.min_word_length:
            return False
        queue = []
        initial_state = LetterBoxedState(
            self.dictionary.prefix_tree, game=self)
        queue.append(initial_state)
        while queue:
            state: LetterBoxedState = queue.pop()
            for edge_index, edge_letters in enumerate(self.board.edge_letters):
                next_states = []
                if state.is_valid_next_edge_index(edge_index):
                    next_states.extend([
                        state.place_letter(letter, edge_index)
                        for letter in edge_letters
                        if state.can_place_letter(letter, edge_index)
                        and s.startswith(state.word_in_progress+letter)
                    ])
                if state.can_finish_word():
                    finished = state.finish_last_word()
                    if finished.words == (s,):
                        return True

                for next_state in next_states:
                    queue.append(next_state)

        return False

    def old_can_be_played_in_game(self, s: str) -> bool:
        # TODO: Make this also take board sides into consideration.
        return len(s) >= self.min_word_length \
            and set(s).issubset(set(self.board.all_letters()))

    def solve(self, strategy='word') -> Iterator[LetterBoxedState]:
        get_child_states = self.get_child_letter_states if strategy == 'letter' else self.get_child_word_states
        queue = PriorityQueue()
        initial_state = LetterBoxedState(
            self.dictionary.prefix_tree, game=self)
        queue.put(initial_state)
        seen = set([initial_state])

        while not queue.empty():
            state: LetterBoxedState = queue.get()
            if state.is_final_state():
                yield state

            for next_state in get_child_states(state):
                if next_state not in seen:
                    queue.put(next_state)
                    if strategy == 'letter':
                      seen.add(next_state)

        # return+yield returns an empty generator instead of None.
        return
        yield


if __name__ == "__main__":
    dictionary = Dictionary.open("word_list.txt")
    letters = input(
        "List all the letters, counterclockwise from the top left corner (for example, BTLEHYVCOIWJ): ").strip() or "BTLEHYVCOIWJ"
    board = LetterBoxedBoard(letters)
    game = LetterBoxedGame(dictionary, board)
    print("I'm thinking...")
    for i, solution in enumerate(game.solve()):
        str_solution = " - ".join(solution.words).upper()
        num_words = len(solution.words)
        num_letters = len(solution.letters)
        num_duplicate_letters = num_letters - game.board.num_dots
        print(f"Solution #{i+1} ({num_words}-solve): {str_solution}")
        print("Stats:")
        print(f"Num words: {num_words}")
        print(f"Num letters: {num_letters}")
        print(f"Num duplicated letters: {num_duplicate_letters}")
        input("Press Enter for another solution")
        print("I'm thinking...")
    print("No more solutions.")
