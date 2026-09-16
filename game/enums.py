from enum import Enum, auto

class Attribute(Enum):
    IGNEOUS = "Igneous"
    ABYSSAL = "Abyssal"
    STORM = "Storm"
    AETHER = "Aether"
    VOID = "Void"


class SkillType(Enum):
    DAMAGE = "Damage"
    HEALING = "Healing"
    PASSIVE = "Passive"


class SealstoneType(Enum):
    FADED = "Faded"
    RUNIC = "Runic"
    ARCANE = "Arcane"
    TWILIGHT = "Twilight"
    PRIMORDIAL = "Primordial"


class EssenceType(Enum):
    GLIMMERING = "Glimmering"
    RADIANT = "Radiant"
    TWILIGHT = "Twilight"
    ECLIPSE = "Eclipse"


class EffectType(Enum):
    BUFF = "Buff"
    DEBUFF = "Debuff"
    STATUS = "Status"


class TargetType(Enum):
    SINGLE_ENEMY = auto()
    ALL_ENEMIES = auto()
    RANDOM_ENEMIES = auto()
    SELF = auto()
    SINGLE_ALLY = auto()
    ALL_ALLIES = auto()

