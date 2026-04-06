const { topKFrequent } = require('../src/solution');

describe('topKFrequent', () => {
  test('basic case', () => {
    const result = topKFrequent([1, 1, 1, 2, 2, 3], 2);
    expect(new Set(result)).toEqual(new Set([1, 2]));
  });

  test('single element', () => {
    expect(topKFrequent([5], 1)).toEqual([5]);
  });

  test('frequency ordering', () => {
    const result = topKFrequent([7, 7, 7, 3, 3, 3, 3, 1, 1], 1);
    expect(result).toEqual([3]);
  });

  test('k equals unique count', () => {
    const result = topKFrequent([1, 2, 3], 3);
    expect(new Set(result)).toEqual(new Set([1, 2, 3]));
  });

  test('negative numbers', () => {
    expect(topKFrequent([-5, -5, 10, 10, 10], 1)).toEqual([10]);
  });

  test('empty array', () => {
    expect(topKFrequent([], 0)).toEqual([]);
  });

  test('k exceeds unique count', () => {
    const result = topKFrequent([1, 1, 2], 5);
    expect(new Set(result)).toEqual(new Set([1, 2]));
  });

  test('k is zero', () => {
    expect(topKFrequent([1, 2, 3], 0)).toEqual([]);
  });

  test('mixed frequencies', () => {
    const result = topKFrequent([1, 1, 1, 2, 2, 3, 3, 3, 3], 2);
    expect(new Set(result)).toEqual(new Set([3, 1]));
  });

  test('large input', () => {
    const nums = Array(200).fill(999).concat(
      Array.from({ length: 100 }, (_, i) => i).flatMap(x => Array(10).fill(x))
    );
    expect(topKFrequent(nums, 1)).toEqual([999]);
  });
});
