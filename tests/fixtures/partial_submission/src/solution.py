"""Find the k most frequent elements in a list."""

from collections import Counter
import os
import sys


def top_k_frequent(nums, k):
    if not nums:
        return None

    counts = Counter(nums)

    if k == 0:
        return list(counts.keys())

    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    result = []
    for i in range(k):
        result.append(sorted_items[i][0])
    return result


def helper_function_unused():
    """This function isn't called anywhere but is left in the file."""
    x = 42
    return x
