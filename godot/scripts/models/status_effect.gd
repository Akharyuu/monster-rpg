class_name StatusEffect
extends RefCounted

var effect_id: String
var effect_name: String
var stat
var effect_type: String
var modifier
var duration: int
var remaining_turns: int
var stacks: int
var max_stacks: int
var source
var modifier_mode: String


func _init(
    p_effect_id: String,
    p_name: String,
    p_stat,
    p_effect_type: String,
    p_modifier,
    p_duration: int,
    p_stacks: int = 1,
    p_max_stacks: int = 1,
    p_source = null,
    p_modifier_mode: String = "multiplicative"
) -> void:
    effect_id = p_effect_id
    effect_name = p_name
    stat = p_stat
    effect_type = p_effect_type
    modifier = p_modifier
    duration = p_duration
    remaining_turns = p_duration
    stacks = p_stacks
    max_stacks = p_max_stacks
    source = p_source
    modifier_mode = p_modifier_mode


func is_active() -> bool:
    return remaining_turns > 0


func reduce_remaining_turns() -> void:
    if remaining_turns > 0:
        remaining_turns -= 1
