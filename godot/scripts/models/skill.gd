class_name Skill
extends RefCounted

var skill_id: String
var skill_name: String
var cooldown: int
var current_cooldown: int = 0


func _init(
    p_skill_id: String,
    p_name: String,
    p_cooldown: int = 0
) -> void:
    skill_id = p_skill_id
    skill_name = p_name
    cooldown = p_cooldown


func is_available() -> bool:
    return current_cooldown == 0


func trigger_cooldown() -> void:
    current_cooldown = cooldown


func reduce_cooldown() -> void:
    if current_cooldown > 0:
        current_cooldown -= 1


func reset_cooldown() -> void:
    current_cooldown = 0
