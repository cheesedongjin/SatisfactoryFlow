from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Node:
    name: str
    base_power: float
    inputs: Dict[str, float]
    outputs: Dict[str, float]
    clock: float = 100.0
    shards: int = 0
    filled_slots: int = 0
    total_slots: int = 0

    def __post_init__(self) -> None:
        self.clock = round(max(0.0, min(self.clock, self.max_clock())), 4)
        if self.shards < 0:
            self.shards = 0

    def max_clock(self) -> float:
        return min(250.0, 100.0 + self.shards * 50.0)

    def power_multiplier(self) -> float:
        if self.total_slots <= 0:
            return 1.0
        return (1 + (self.filled_slots / self.total_slots)) ** 2

    def power_usage(self) -> float:
        base = self.base_power
        multiplier = self.power_multiplier()
        usage = base * multiplier * ((self.clock / 100) ** 1.321928)
        return usage

    def production_factor(self) -> float:
        return (self.clock / 100.0) * self.power_multiplier()

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "base_power": self.base_power,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "clock": self.clock,
            "shards": self.shards,
            "filled_slots": self.filled_slots,
            "total_slots": self.total_slots,
        }

    @staticmethod
    def from_dict(d: Dict) -> "Node":
        return Node(
            name=d.get("name", ""),
            base_power=d.get("base_power", 0.0),
            inputs=d.get("inputs", {}),
            outputs=d.get("outputs", {}),
            clock=d.get("clock", 100.0),
            shards=d.get("shards", 0),
            filled_slots=d.get("filled_slots", 0),
            total_slots=d.get("total_slots", 0),
        )

