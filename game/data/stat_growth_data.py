# Stats affected by level growth.
#
# These multipliers are applied to the final stats defined
# in MONSTER_DATA.
#
# MONSTER_DATA therefore represents:
#
#     Level 50 + Ascended
#
# Crit Rate, Crit Damage, Accuracy and Resistance do not
# scale with level.

LEVEL_STAT_MULTIPLIER = {
    1: 0.3500,
    2: 0.3611,
    3: 0.3722,
    4: 0.3833,
    5: 0.3944,
    6: 0.4056,
    7: 0.4167,
    8: 0.4278,
    9: 0.4389,
    10: 0.4500,

    11: 0.4620,
    12: 0.4740,
    13: 0.4860,
    14: 0.4980,
    15: 0.5100,
    16: 0.5220,
    17: 0.5340,
    18: 0.5460,
    19: 0.5580,
    20: 0.5700,

    21: 0.5830,
    22: 0.5960,
    23: 0.6090,
    24: 0.6220,
    25: 0.6350,
    26: 0.6480,
    27: 0.6610,
    28: 0.6740,
    29: 0.6870,
    30: 0.7000,

    31: 0.7120,
    32: 0.7240,
    33: 0.7360,
    34: 0.7480,
    35: 0.7600,
    36: 0.7720,
    37: 0.7840,
    38: 0.7960,
    39: 0.8080,
    40: 0.8200,
}


# Ascension gives an immediate stat jump at level 40:
#
#     normal lvl 40   → 82%
#     ascended lvl 40 → 85%
#
# Levels 41–50 then grow towards 100%.

ASCENDED_STAT_MULTIPLIER = {
    40: 0.850,
    41: 0.865,
    42: 0.880,
    43: 0.895,
    44: 0.910,
    45: 0.925,
    46: 0.940,
    47: 0.955,
    48: 0.970,
    49: 0.985,
    50: 1.000,
}