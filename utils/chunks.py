from collections.abc import Sequence, Iterator
from typing import TypeVar

T = TypeVar("T")


def chunks(items: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]