from __future__ import print_function

def normalize_signal_batch(readings):
    """Scale raw sensor readings into a stable 0..1 range."""
    if not readings:
        return []
    peak = max(abs(r) for r in readings) or 1.0
    return [round(float(r) / peak, 4) for r in readings]


def detect_threshold_crossings(readings, threshold):
    crossings = []
    for idx, value in enumerate(readings):
        if value >= threshold:
            crossings.append(idx)
    return crossings


class SignalWindow(object):
    def __init__(self, size):
        self.size = size
        self.buffer = []

    def push(self, value):
        self.buffer.append(value)
        if len(self.buffer) > self.size:
            self.buffer.pop(0)

    def average(self):
        if not self.buffer:
            return 0.0
        return sum(self.buffer) / float(len(self.buffer))

    def max_value(self):
        if not self.buffer:
            return 0.0
        return max(self.buffer)
