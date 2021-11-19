import codecs
from typing import Union

ZD_NEGS = {
    '}': 0,
    'J': 1,
    'K': 2,
    'L': 3,
    'M': 4,
    'N': 5,
    'O': 6,
    'P': 7,
    'Q': 8,
    'R': 9
}
Number = Union[float, int]


def x_format(stream: bytes, decimals: int) -> None:
    return None


def c_format(stream: bytes, decimals: int) -> str:
    result = codecs.getdecoder('utf-8')(stream)
    return result[0]


def v_format(stream: bytes, decimals: int) -> str:
    return c_format(stream, decimals).rstrip()


def zd_format(stream: bytes, decimals: int) -> Number:
    result = codecs.getdecoder('utf-8')(stream)[0]
    result = result.replace(' ', '0')
    if result[-1] in ZD_NEGS:
        result = f'-{result[:-1]}{ZD_NEGS[result[-1]]}'

    if not decimals:
        return int(result)
    else:
        dec_pos = len(result) - decimals
        return float(result[:dec_pos] + '.' + result[dec_pos:])


def pd_format(stream: bytes, decimals: int) -> Number:
    n = ['']
    for b in stream[:-1]:
        hi, lo = divmod(b, 16)
        n.append(str(hi))
        n.append(str(lo))

    digit, sign = divmod(stream[-1], 16)
    n.append(str(digit))
    if sign == 13:
        n[0] = '-'
    else:
        n[0] = '+'
    if decimals:
        decimals = 0 - decimals
        n.insert(decimals, '.')
        return float(''.join(n))
    else:
        return int(''.join(n))


def bh_format(stream: bytes, decimals: int) -> Number:
    total = 0
    enum = len(stream)

    for i in stream:
        enum -= 1
        # bit shift to concatenate the bits
        # to create an n * 8 bit integer
        total += i << (enum * 8)
    total = twos_complement(total, len(stream) * 8)

    if decimals:
        as_str = str(total)
        decimals = 0 - decimals
        return float(f'{as_str[:decimals]}.{as_str[decimals:]}')
    else:
        return total


def twos_complement(val: int, bits: int) -> int:
    """
    returns the two's complement
    of the integer passed in.
    bits arg needed to determine the first bit
    """
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val
