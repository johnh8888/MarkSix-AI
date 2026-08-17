# -*- coding: utf-8 -*-
from collections import Counter
from .config import NUMBER_TO_WAVE

def get_special(row):
    try: return int(row.get('special', row.get('numbers', '').split(',')[-1]))
    except Exception: return 0

def special_frequency(rows, window=None):
    sp=[get_special(r) for r in (rows[:window] if window else rows) if 1<=get_special(r)<=49]
    c=Counter(sp); return {n:c.get(n,0) for n in range(1,50)}

def special_omission(rows, cap=60):
    sp=[get_special(r) for r in rows if 1<=get_special(r)<=49]
    out={}; seen=set()
    for i,n in enumerate(sp):
        if n not in seen: out[n]=i; seen.add(n)
    return {n:min(cap,out.get(n,cap))/cap for n in range(1,50)}

def wave_counts(rows, window=30):
    c=Counter(NUMBER_TO_WAVE.get(get_special(r)) for r in rows[:window]); c.pop(None,None); return c
