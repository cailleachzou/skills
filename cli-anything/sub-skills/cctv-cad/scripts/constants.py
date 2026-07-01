"""传感器尺寸、DORI 标准、默认俯角常量"""

SENSORS = {
    "1/3":   {"w": 4.8,   "h": 3.6},
    "1/2.8": {"w": 5.12,  "h": 3.84},
    "1/2.7": {"w": 5.3,   "h": 4.0},
    "1/2.5": {"w": 5.76,  "h": 4.32},
    "1/2":   {"w": 6.4,   "h": 4.8},
    "1/1.8": {"w": 7.18,  "h": 5.4},
    "1/1.7": {"w": 7.6,   "h": 5.7},
    "2/3":   {"w": 8.8,   "h": 6.6},
}

DORI = {
    "I": {"name": "辨识", "px_per_m": 250, "color": 1},
    "R": {"name": "识别", "px_per_m": 125, "color": 30},
    "O": {"name": "观察", "px_per_m": 62,  "color": 2},
    "D": {"name": "探测", "px_per_m": 25,  "color": 3},
}

PIXELS = {
    "2mp": 1920,
    "4mp": 2560,
    "8mp": 3840,
}

DEFAULT_TILT = {
    2.8: 25,
    4:   30,
    6:   35,
    8:   40,
    12:  50,
}

LAYER_COLORS = {
    "CAMERA":     7,
    "FOV":        4,
    "DORI-I":     1,
    "DORI-R":     30,
    "DORI-O":     2,
    "DORI-D":     3,
    "BLINDSPOT":  1,
    "ANNOTATION": 8,
}

SCALE_INTERVAL = 5
