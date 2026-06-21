from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Mode:
    frequency: float      # Frequency in Hz
    amplitude: float      # Initial amplitude (A_i)
    decay_rate: float     # Exponential decay rate (d_i) in 1/s
    phase: float = 0.0    # Initial phase in radians

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Mode:
        return cls(
            frequency=float(data["frequency"]),
            amplitude=float(data["amplitude"]),
            decay_rate=float(data["decay_rate"]),
            phase=float(data.get("phase", 0.0))
        )


class ModeList:
    def __init__(self, modes: list[Mode] = None) -> None:
        self.modes = modes if modes is not None else []

    def add(self, mode: Mode) -> None:
        self.modes.append(mode)

    def sort(self, by: str = "amplitude", reverse: bool = True) -> None:
        """Sorts modes in-place by a field name."""
        if by not in ["amplitude", "frequency", "decay_rate"]:
            raise ValueError(f"Cannot sort by field '{by}'")
        self.modes.sort(key=lambda m: getattr(m, by), reverse=reverse)

    def threshold(self, min_amp: float) -> ModeList:
        """Returns a new ModeList containing modes with amplitude >= min_amp."""
        return ModeList([m for m in self.modes if m.amplitude >= min_amp])

    def limit(self, count: int) -> ModeList:
        """Returns a new ModeList with at most 'count' modes, sorting by amplitude first."""
        temp = ModeList(list(self.modes))
        temp.sort(by="amplitude", reverse=True)
        return ModeList(temp.modes[:count])

    def to_list_of_dicts(self) -> list[dict]:
        return [m.to_dict() for m in self.modes]

    @classmethod
    def from_list_of_dicts(cls, data: list[dict]) -> ModeList:
        return cls([Mode.from_dict(d) for d in data])

    def save_json(self, path: Path | str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_list_of_dicts(), f, indent=2)

    @classmethod
    def load_json(cls, path: Path | str) -> ModeList:
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_list_of_dicts(data)

    def __len__(self) -> int:
        return len(self.modes)

    def __getitem__(self, index: int) -> Mode:
        return self.modes[index]
