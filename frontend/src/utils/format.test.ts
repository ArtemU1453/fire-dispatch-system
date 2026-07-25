import { describe, expect, it } from 'vitest';

import {
  confidenceLabel,
  formatCoords,
  formatDistance,
  formatDuration,
  statusLabel,
} from './format';

describe('format utils', () => {
  it('formats distance in m and km', () => {
    expect(formatDistance(450)).toBe('450 м');
    expect(formatDistance(5300)).toBe('5.3 км');
    expect(formatDistance(null)).toBe('—');
  });

  it('formats duration', () => {
    expect(formatDuration(45)).toBe('45 с');
    expect(formatDuration(360)).toBe('6 мин');
    expect(formatDuration(3660)).toBe('1 ч 1 мин');
    expect(formatDuration(null)).toBe('—');
  });

  it('formats coordinates', () => {
    expect(formatCoords(55.75391, 37.62082)).toBe('55.75391, 37.62082');
    expect(formatCoords(null, null)).toBe('—');
  });

  it('localizes labels', () => {
    expect(confidenceLabel('high')).toBe('высокая');
    expect(statusLabel('no_resources')).toBe('Ресурсы не найдены');
  });
});
