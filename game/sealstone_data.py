from .enums import Attribute, SealstoneType

SEALSTONE_DATA = {
    SealstoneType.FADED: {
        "allowed_attributes": [
            Attribute.IGNEOUS,
            Attribute.ABYSSAL,
            Attribute.STORM
        ],
        "rarities": {
            1: 60,
            2: 30,
            3: 10
        }
    },
    SealstoneType.RUNIC: {
        "allowed_attributes": [
            Attribute.IGNEOUS,
            Attribute.ABYSSAL,
            Attribute.STORM
        ],
        "rarities": {
            3: 87,
            4: 12.2,
            5: 0.8
        }
    },
    SealstoneType.ARCANE: {
        "allowed_attributes": [
            Attribute.IGNEOUS,
            Attribute.ABYSSAL,
            Attribute.STORM
        ],
        "rarities": {
            4: 91.5,
            5: 8.5
        }
    },
    SealstoneType.TWILIGHT: {
        "allowed_attributes": [
            Attribute.AETHER,
            Attribute.VOID
        ],
        "rarities": {
            3: 89,
            4: 10.6,
            5: 0.4
        }
    },
    SealstoneType.PRIMORDIAL: {
        "allowed_attributes": [
            Attribute.AETHER,
            Attribute.VOID
        ],
        "rarities": {
            4: 94,
            5: 6
        }
    }   
}

