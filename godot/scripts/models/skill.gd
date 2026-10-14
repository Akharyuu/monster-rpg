class_name Skill
extends RefCounted

var skill_id: String
var skill_name: String
var cooldown: int
var current_cooldown: int = 0
var target_type: String = "single_enemy"


func _init(
    p_skill_id: String,
    p_name: String,
    p_cooldown: int = 0,
    p_target_type: String = "single_enemy"
) -> void:
    skill_id = p_skill_id
    skill_name = p_name
    cooldown = p_cooldown
    target_type = p_target_type


func is_available() -> bool:
    return current_cooldown == 0


func trigger_cooldown() -> void:
    current_cooldown = cooldown


func reduce_cooldown() -> void:
    if current_cooldown > 0:
        current_cooldown -= 1


func reset_cooldown() -> void:
    current_cooldown = 0
