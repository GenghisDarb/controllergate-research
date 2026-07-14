from __future__ import annotations


class CircuitBreaker:
    def __init__(self, threshold: int = 2):
        self.threshold = threshold
        self.failures = 0
        self.open = False

    def record(self, success: bool) -> str:
        if success:
            self.failures = 0
            self.open = False
        else:
            self.failures += 1
            self.open = self.failures >= self.threshold
        return "OPEN" if self.open else "CLOSED"
