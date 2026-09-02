from enum import Enum

class Attribute(Enum):
    IGNEOUS = "Igneous"
    ABYSSAL = "Abyssal"
    STORM = "Storm"
    AETHER = "Aether"
    VOID = "Void"


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