#!/usr/bin/env python3
from decimal import Decimal, ROUND_HALF_UP
import re, sys

def normalize_amount_to_cents(value):
    if value is None:
        raise ValueError('empty amount is not zero')
    s = str(value).strip()
    if s in ['', '-', '—', '########']:
        raise ValueError('invalid blank amount')
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1]
    s = s.replace(',', '').replace('，','').replace('元','').strip()
    multiplier = Decimal('1')
    if '万元' in s or s.endswith('万'):
        s = s.replace('万元','').replace('万','')
        multiplier = Decimal('10000')
    if s.startswith('-'):
        negative = True
        s = s[1:]
    if not re.fullmatch(r'\d+(\.\d+)?', s):
        raise ValueError(f'invalid amount: {value!r}')
    cents = (Decimal(s) * multiplier * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    cents = int(cents)
    return -cents if negative else cents

def zero_delta(expected_cents, actual_cents):
    return int(expected_cents) == int(actual_cents)

if __name__ == '__main__':
    cases = [('1,234.56',123456), ('(1,234.56)',-123456), ('1.00万',1000000), ('-2.01',-201)]
    for raw, exp in cases:
        got = normalize_amount_to_cents(raw)
        if got != exp:
            print('FAIL', raw, got, exp); sys.exit(1)
    if zero_delta(100,101):
        print('FAIL delta not detected'); sys.exit(1)
    print('PASS: zero delta reference checks passed')
