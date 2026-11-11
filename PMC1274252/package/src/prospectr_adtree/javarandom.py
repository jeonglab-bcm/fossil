"""java.util.Random, bit for bit, for Weka's shuffles and fold assignment."""

_MULT = 0x5DEECE66D
_MASK = (1 << 48) - 1


def _int32(x: int) -> int:
    x &= 0xFFFFFFFF
    return x - (1 << 32) if x & 0x80000000 else x


class JavaRandom:
    def __init__(self, seed: int):
        self.seed = (seed ^ _MULT) & _MASK

    def _next(self, bits: int) -> int:
        self.seed = (self.seed * _MULT + 0xB) & _MASK
        return _int32(self.seed >> (48 - bits))

    def next_int(self, bound: int) -> int:
        if bound <= 0:
            raise ValueError("bound must be positive")
        if bound & -bound == bound:
            return _int32((bound * self._next(31)) >> 31)
        while True:
            bits = self._next(31)
            val = bits % bound
            if _int32(bits - val + (bound - 1)) >= 0:
                return val
