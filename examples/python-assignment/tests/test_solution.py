"""Instructor-provided tests for the k-most-frequent-elements problem."""

from src.solution import top_k_frequent


class TestTopKFrequent:

    def test_basic_case(self):
        result = top_k_frequent([1, 1, 1, 2, 2, 3], 2)
        assert set(result) == {1, 2}

    def test_single_element(self):
        assert top_k_frequent([5], 1) == [5]

    def test_frequency_ordering(self):
        result = top_k_frequent([7, 7, 7, 3, 3, 3, 3, 1, 1], 1)
        assert result == [3]

    def test_k_equals_unique(self):
        result = top_k_frequent([1, 2, 3], 3)
        assert set(result) == {1, 2, 3}

    def test_negative_numbers(self):
        result = top_k_frequent([-5, -5, 10, 10, 10], 1)
        assert result == [10]

    def test_empty_list(self):
        assert top_k_frequent([], 0) == []

    def test_k_exceeds_unique(self):
        result = top_k_frequent([1, 1, 2], 5)
        assert set(result) == {1, 2}

    def test_k_zero(self):
        assert top_k_frequent([1, 2, 3], 0) == []

    def test_mixed_frequencies(self):
        result = top_k_frequent([1, 1, 1, 2, 2, 3, 3, 3, 3], 2)
        assert set(result) == {3, 1}

    def test_large_input(self):
        nums = [999] * 200 + list(range(100)) * 10
        result = top_k_frequent(nums, 1)
        assert result == [999]
