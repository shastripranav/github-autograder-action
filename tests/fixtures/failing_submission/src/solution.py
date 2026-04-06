"""Find the k most frequent elements in a list."""

import os, sys, json
from collections import *


def top_k_frequent(nums,k):
    if not nums:
        return None
    freq = {}
    for n in nums:
            freq[n] = freq.get(n, 0) + 1
    return [n for n, count in freq.items() if count >= k]


def unused_func():
    x=1
    y=2
    z=3
    return


def another_unused():
    pass
