from __future__ import annotations
from typing import Dict, Sequence, Iterator, Callable, TypeAlias

class Dictionary(object):
  END_TOKEN = "ø"
  Trie: TypeAlias = Dict[str, Dict]
  """
    A valid `Trie` is a dictionary (mapping `str -> Trie`) with the following properties:
    - Each key is either a lowercase alphanumeric character or the `END_TOKEN` (`ø`).
    - Leaf nodes (end of word) are represented as a mapping from `ø` to an empty `dict`. No other key may map to an empty `dict`.
    - A Trie cannot be recursively constructed.
    """

  def __init__(self, word_list: Sequence[str]):
    self._word_set = set(word.lower() for word in word_list)
    self.prefix_tree = Dictionary._build_prefix_tree(self._word_set)

  def __len__(self) -> int:
    return len(self._word_set)

  def __contains__(self, word: str) -> bool:
    return word.lower() in self._word_set
  
  def __iter__(self) -> Iterator[str]:
    return self._word_set.__iter__()
  
  def filter(self, predicate: Callable[[str], bool]) -> Dictionary:
    return Dictionary(list(filter(predicate, self._word_set)))


  @staticmethod
  def _insert_into_prefix_trie(
      trie: Dictionary.Trie, word: str
  ) -> None:
    for c in word:
      if c not in trie:
        trie[c] = {}
      trie = trie[c]
    trie[Dictionary.END_TOKEN] = {}

  @staticmethod
  def _build_prefix_tree(words: Sequence[str]) -> Dictionary.Trie:
    trie = {}
    for word in words:
      Dictionary._insert_into_prefix_trie(trie, word)
    return trie

  @staticmethod
  def open(fname: str):
    with open(fname) as file:
      words = [Dictionary._sanitize_line(line) for line in file]
      return Dictionary(words)

  @staticmethod
  def _sanitize_line(line: str) -> str:
    return "".join(c.lower() for c in line if c.isalpha())