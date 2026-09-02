from .ui import select_skill
import random

def battle(player, enemy):

    while player.is_alive and enemy.is_alive:

        #Orden de turno
        if player.speed > enemy.speed:
            first = player
            second = enemy

        elif player.speed < enemy.speed:
            first = enemy
            second = player

        else:
            first = random.choice([player, enemy])
            if first == player:
                second = enemy
            else:
                second = player

        #Primero
        if first == player:
            outcome = player_turn(player, enemy)
        else: 
            outcome = enemy_turn(enemy, player)

        if outcome is not None:
            return outcome

        #Segundo
        if second == player:
            outcome = player_turn(player, enemy)
        else: 
            outcome = enemy_turn(enemy, player)

        if outcome is not None:
            return outcome

        print("Ally:")
        player.show()

        print("Enemy")
        enemy.show()


def player_turn(player, enemy):

    while True:

        decision = input("¿Qué quieres hacer? (Atacar: 'a' / Salir: 's')\n> ")

        #Ataque
        if decision == "a":
            skill = select_skill(player)
            damage, critical = player.use_skill(enemy, skill)
            if critical: 
                print(f"CRÍTICO! El {enemy.name} enemigo ha recibido {damage} puntos de daño.")
            else: 
                print(f"El {enemy.name} enemigo ha recibido {damage} puntos de daño.")
            if not enemy.is_alive:
                print(f"El {enemy.name} enemigo ha sido derrotado.")
                return "victoria"
            return None

        #Salir
        elif decision == "s":
            return "huida"

        else:
            print("Opción inválida.")
            continue


def enemy_turn(enemy, player):
    enemy_skill = enemy.get_skill(1)

    if enemy_skill is not None:
        damage, critical = enemy.use_skill(player, enemy_skill)
        if critical:
            print(f"CRÍTICO! El {player.name} aliado ha recibido {damage} puntos de daño.")
        else:
            print(f"El {player.name} aliado ha recibido {damage} puntos de daño.")

        if not player.is_alive:
            print(f"El {player.name} ha sido derrotado.")
            return "derrota"

    return None
               
