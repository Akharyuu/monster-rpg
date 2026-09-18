import json

from .serializers import player_to_dict
from .deserializers import player_from_dict


def save_player(player, file_path):

    player_data = player_to_dict(player)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            player_data,
            file,
            indent=4,
            ensure_ascii=False
        )


def load_player(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        player_data = json.load(file)

    return player_from_dict(player_data)