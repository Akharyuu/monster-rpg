class_name Monster
extends RefCounted

const SkillScript = preload("res://scripts/models/skill.gd")

var monster_id: String
var monster_name: String
var family: String
var attribute: String
var rarity: int

var level: int = 1
var ascended: bool = false

var max_health: int
var health: int
var attack: int
var defense: int
var speed: int

var accuracy: float = 25.0
var resistance: float = 25.0
var crit_rate: float = 15.0
var crit_damage: float = 50.0

var action_gauge: float = 0.0
var skills: Array = []


func _init(
    p_monster_id: String,
    p_name: String,
    p_family: String,
    p_attribute: String,
    p_rarity: int,
    p_max_health: int,
    p_attack: int,
    p_defense: int,
    p_speed: int,
    p_skills: Array = []
) -> void:
    monster_id = p_monster_id
    monster_name = p_name
    family = p_family
    attribute = p_attribute
    rarity = p_rarity

    max_health = p_max_health
    health = p_max_health
    attack = p_attack
    defense = p_defense
    speed = p_speed
    skills = p_skills


func is_alive() -> bool:
    return health > 0


func get_effective_stat(stat: String) -> float:
    match stat:
        "max_health", "health":
            return max_health
        "attack":
            return attack
        "defense":
            return defense
        "speed":
            return speed
        "accuracy":
            return accuracy
        "resistance":
            return resistance
        "crit_rate":
            return crit_rate
        "crit_damage":
            return crit_damage
        _:
            push_error("Unknown stat: %s" % stat)
            return 0.0


func get_attribute_modifier(defender) -> float:
    if (
        (attribute == "igneous" and defender.attribute == "abyssal")
        or (attribute == "abyssal" and defender.attribute == "storm")
        or (attribute == "storm" and defender.attribute == "igneous")
    ):
        return 0.85

    if (
        (attribute == "igneous" and defender.attribute == "storm")
        or (attribute == "abyssal" and defender.attribute == "igneous")
        or (attribute == "storm" and defender.attribute == "abyssal")
    ):
        return 1.15

    return 1.0


func receive_damage(amount: int) -> int:
    var actual_damage: int = mini(amount, health)
    health = maxi(0, health - amount)
    return actual_damage


func heal(amount: int) -> int:
    if not is_alive():
        return 0

    var old_health: int = health
    health = mini(max_health, health + amount)
    return health - old_health


func get_skill(index: int):
    if index < 1 or index > skills.size():
        return null

    return skills[index - 1]


func reduce_skill_cooldowns() -> void:
    for skill in skills:
        skill.reduce_cooldown()
