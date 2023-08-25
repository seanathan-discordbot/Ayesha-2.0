class Modifier:
    def __init__(self, magnitude: int = 0, multiplier: float = 0) -> None:
        self.magnitude = magnitude
        self.multiplier = multiplier
        self.final = 0
    
    def apply(self):
        self.final = int(self.magnitude * self.multiplier)