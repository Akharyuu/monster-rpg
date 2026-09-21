from .player import Player
#from game.models.enums import SealstoneType


def create_new_game(name):

    player = Player(name)

    #player.inventory.add_item(SealstoneType.ARCANE, 3)

    return player