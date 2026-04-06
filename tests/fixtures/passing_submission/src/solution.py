"""Find the k most frequent elements in a list."""

from collections import Counter
import heapq


def top_k_frequent(nums: list[int], k: int) -> list[int]:
    """Return the k most frequently occurring elements.

    Uses a min-heap of size k for O(n log k) performance on large inputs.
    """
    if not nums or k <= 0:
        return []

    counts = Counter(nums)

    # heapq.nlargest handles the k > unique elements case gracefully
    k = min(k, len(counts))
    return heapq.nlargest(k, counts, key=counts.get)


def top_k_frequent_bucket(nums: list[int], k: int) -> list[int]:
    """Bucket sort approach — O(n) time, O(n) space."""
    if not nums or k <= 0:
        return []

    counts = Counter(nums)
    buckets: list[list[int]] = [[] for _ in range(len(nums) + 1)]

    for num, freq in counts.items():
        buckets[freq].append(num)

    result = []
    for i in range(len(buckets) - 1, -1, -1):
        for num in buckets[i]:
            result.append(num)
            if len(result) == k:
                return result

    return result
