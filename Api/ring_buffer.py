from typing import Generic, TypeVar, Optional, Iterator, Any

T = TypeVar("T")  # Generic type for the _buffer


class Ringbuffer(Generic[T]):
    def __init__(self, _size: int):
        """
        Initializes a ring _buffer with the specified _size.
        """
        self._size = _size
        self._buffer: list[Optional[T]] = [None] * _size  # Fix: use [None] * _size, not [] * _size
        self._position = 0
        self._count = 0
        self._add_count = 0
        self._version = 0
        self._is_fallout_valid = False

    @property
    def is_buffer_valid(self) -> bool:
        """
        Returns True if the _buffer is full (_count == _size).
        """
        return self._count == self._size

    def __getitem__(self, rel_pos: int) -> Optional[T]:
        if self._count < 1:
            raise IndexError("Must add a ring _buffer slot after initialization")
        if rel_pos < 0 or rel_pos >= self._size:
            raise IndexError("Index out of range")
        return self._buffer[(self._position + self._size - rel_pos - 1) % self._size]

    def __setitem__(self, rel_pos: int, value: T):
        if self._count < 1:
            raise IndexError("Must add a ring _buffer slot after initialization")
        self._buffer[(self._position + self._size - rel_pos - 1) % self._size] = value

    def get_abs_pos(self, rel_pos: int) -> int:
        """
        Gets the absolute _position from the relative _position.
        """
        return (self._position + self._size - self._count + rel_pos) % self._size

    def add(self, item: T):
        """
        Adds a new item to the _buffer.
        """
        self.add_with_details(item, out_ndx=False, out_fallout=False)

    def add_with_details(self, item: T, out_ndx: bool = False, out_fallout: bool = False) -> Any:
        """
        Adds a new item to the _buffer and returns details (index, fallout).
        """
        ndx = self._position
        fall_out = self._buffer[self._position]

        self._buffer[self._position] = item
        self._position = (self._position + 1) % self._size

        if self._count < self._size:
            self._count += 1

        self._version += 1
        self._add_count += 1

        if not self._is_fallout_valid and self._add_count > self._size:
            self._is_fallout_valid = True

        if out_ndx and out_fallout:
            return ndx, fall_out
        elif out_ndx:
            return ndx
        elif out_fallout:
            return fall_out

    def clear(self):
        """
        Clears the _buffer.
        """
        self._buffer = [None] * self._size
        self._position = 0
        self._count = 0
        self._version += 1

    def contains(self, item: T) -> bool:
        """
        Checks if the _buffer contains the specified item.
        """
        return self.index_of(item) != -1

    def index_of(self, item: T) -> int:
        """
        Returns the index of the specified item in the _buffer, or -1 if not found.
        """
        for i in range(self._count):
            buffer_item = self._buffer[(self._position - self._count + i) % self._size]
            if buffer_item == item:
                return i
        return -1

    # def copy_to(self, array: List[T], array_index: int, cnt: int):
    #     """
    #     Copies items from the _buffer to the specified array.
    #     """
    #     for i in range(cnt):
    #         array[i + array_index] = self._buffer[(self._position - self._count + i) % self._size]

    def __iter__(self) -> Iterator[T]:
        """
        Returns an iterator over the _buffer.
        """
        _version = self._version
        for i in range(self._count):
            if _version != self._version:
                raise RuntimeError("Collection changed during iteration")
            yield self[i]  # type: ignore

    def remove(self, item: T) -> bool:
        """
        Removes the specified item from the _buffer.
        """
        index = self.index_of(item)
        if index == -1:
            return False
        self.remove_at(index)
        return True

    def remove_at(self, index: int):
        """
        Removes the item at the specified index.
        """
        if index < 0 or index >= self._count:
            raise IndexError("Index out of range")
        for i in range(index, self._count - 1):
            self._buffer[(self._position - self._count + i) % self._size] = self._buffer[
                (self._position - self._count + i + 1) % self._size
            ]
        self._buffer[(self._position - 1) % self._size] = None
        self._position -= 1
        self._count -= 1
        self._version += 1

    def lowest(self) -> Optional[T]:
        """
        Returns the lowest value in the _buffer (requires items to be comparable).
        """
        if not self._count:
            return None
        return min(self._buffer[: self._count])  # type: ignore

    def highest(self) -> Optional[T]:
        """
        Returns the highest value in the _buffer (requires items to be comparable).
        """
        if not self._count:
            return None
        return max(self._buffer[: self._count])  # type: ignore

    def first(self) -> Optional[T]:
        """
        Returns the first item added to the _buffer.
        """
        if not self._count:
            return None
        return self[self._count - 1]

    def last(self) -> Optional[T]:
        """
        Returns the last item added to the _buffer.
        """
        if not self._count:
            return None
        return self[0]
