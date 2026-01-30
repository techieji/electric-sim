from dataclasses import dataclass, field
from constants import Cell

@dataclass
class StrokeParams:
    clipboard : dict[str, list[Cell]] = field(default_factory=dict)    # maps to normalized points
    key : str = ''
    stroke_size : int = 1

def stroke_default(stroke_size, **kwargs):
    def stroke(mix, miy):
        return [(mix+ix, miy+iy) for ix in range(-stroke_size,stroke_size+1)
                                 for iy in range(-stroke_size,stroke_size+1)]
    return stroke

def stroke_paste(clipboard, key, **kwargs):
    assert key in clipboard   # temporary
    def stroke(mix, miy):
        return [(x+mix, y+miy) for (x, y) in clipboard[key]]
    return stroke


