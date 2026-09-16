import random
from .enums import SkillType, EffectType, TargetType
from .status_effect_data import STATUS_EFFECT_DATA
from .status_effect import StatusEffect
from .passive_handlers import PASSIVE_HANDLERS
from .passive_triggers import trigger_passives
from .skill_damage_handlers import DAMAGE_HANDLERS
from .skill_after_handlers import AFTER_SKILL_HANDLERS
from .skill_on_hit_handlers import ON_HIT_HANDLERS
from .skill_effect_conditions import EFFECT_CONDITIONS

class Skill:
    def __init__(self, skill_id, name, target_type=None, cooldown=0):
        self.skill_id = skill_id
        self.name = name
        self.target_type = target_type
        self.cooldown = cooldown
        self.current_cooldown = 0


    def is_available(self):
        return self.current_cooldown == 0


    def trigger_cooldown(self):
        self.current_cooldown = self.cooldown


    def reduce_cooldown(self):
        self.current_cooldown -= 1

        if self.current_cooldown < 0:
            self.current_cooldown = 0


    def __eq__(self, other):
        return isinstance(other, Skill) and self.skill_id == other.skill_id


    def __repr__(self):
        return f"Skill({self.name, self.cooldown})"



class DamageSkill(Skill):
    def __init__(self, skill_id, name, multiplier, hits, hit_multipliers, target_type, scaling_stat="attack", 
                 cooldown=0, damage_handler=None, damage_handler_data=None, on_hit_handlers=None, after_skill_handlers=None, effects=None):
        super().__init__(skill_id, name, target_type, cooldown)
        self.skill_type = SkillType.DAMAGE
        self.multiplier = multiplier
        self.hits = hits
        self.hit_multipliers = hit_multipliers

        if self.hit_multipliers and len(self.hit_multipliers) != self.hits:
            raise ValueError(
                f"{self.name}: hit_multipliers must contain "
                f"{self.hits} values."
            )

        self.scaling_stat = scaling_stat
        self.damage_handler = damage_handler
        self.damage_handler_data = damage_handler_data

        self.on_hit_handlers = (
            on_hit_handlers
            if on_hit_handlers is not None
            else []
        )

        self.after_skill_handlers = (
            after_skill_handlers
            if after_skill_handlers is not None
            else []
        )

        if effects is not None:
            self.effects = effects
        else: 
            self.effects = []


    def damage_calc(self, attacker, defender, hit_multiplier):
            critical = False

            #Gets the effective scaling stat for the skill and applies it to calc raw damage
            scaling_stat = self.scaling_stat
            effective_scaling_stat = attacker.get_effective_stat(scaling_stat)

            #Normalize max_health stat to be in the same scale as other stats
            if scaling_stat == "max_health":
                effective_scaling_stat *= 0.08

            #Manages the skill bonus damage calling to the respective handler, if there is one
            damage_data = {}
            
            if self.damage_handler:
                handler = DAMAGE_HANDLERS[self.damage_handler]
                damage_data = handler(attacker, defender, self)

            bonus_damage = damage_data.get("damage_multiplier", 1)
            ignore_defense = damage_data.get("ignore_defense", False)

            raw_damage = effective_scaling_stat * self.multiplier * bonus_damage * hit_multiplier

            if raw_damage <= 0:
                return 1, critical

            #Gets % damage reduction based on defense
            damage_reduction = 1

            if not ignore_defense:
                effective_defense = defender.get_effective_stat("defense")

                damage_reduction = 1000 / (1000 + effective_defense)

            #Attribute Advantage
            attribute_modifier = attacker.get_attribute_modifier(defender)
    
            #Crit Roll
            critical_damage_bonus = 1

            if random.randint(1, 100) <= attacker.get_effective_stat("crit_rate"):
                critical_damage_bonus += attacker.crit_damage / 100
                critical = True

            #Final damage
            final_damage = raw_damage * damage_reduction * attribute_modifier * critical_damage_bonus

            return int(final_damage), critical


    def execute(self, caster, targets):
        target_results = []

        # Random enemies case
        if self.target_type == TargetType.RANDOM_ENEMIES:

            random_target_results = {}

            for hit in range(self.hits):
                alive_targets = [target for target in targets if target.is_alive]

                if not alive_targets:
                    break

                target = random.choice(alive_targets)

                if target not in random_target_results:
                    random_target_results[target] = {
                        "target": target,
                        "total_damage": 0,
                        "any_critical": False,
                        "hit_results": [],
                        "effects_applied": [],
                        "snapshot": self.get_target_snapshot(target)
                    }

                current_result = random_target_results[target]

                hit_multiplier = 1.0

                if self.hit_multipliers:
                    hit_multiplier = self.hit_multipliers[hit]

                damage, critical = self.damage_calc(caster, target, hit_multiplier)

                broken_effects = target.receive_damage(
                    damage,
                    source=caster
                )

                for broken_effect in broken_effects:

                    if (
                        broken_effect.effect_id == "freeze"
                        and broken_effect.source is not None
                    ):
                        trigger_passives(
                            "freeze_broken_by_damage",
                            broken_effect.source,
                            {
                                "attacker": caster,
                                "target": target,
                                "skill": self,
                                "broken_effect": broken_effect
                            }
                        )

                # Skill on-hit handlers
                for handler_config in self.on_hit_handlers:
                    handler_name = handler_config["handler"]
                    data = handler_config.get("data", {})

                    handler = ON_HIT_HANDLERS[handler_name]

                    handler(
                        caster,
                        target,
                        self,
                        data
                    )

                current_result["total_damage"] += damage

                current_result["hit_results"].append(
                    {
                        "damage": damage,
                        "critical": critical
                    }
                )

                if critical:
                    current_result["any_critical"] = True

                # Passive on_hit handler
                context = {
                    "target": target
                }

                trigger_passives(
                    "on_hit",
                    caster,
                    context
                )

                # Passive per-hit handler
                for effect in self.effects:
                    if effect.get("trigger", "after_skill") == "per_hit":

                        applied_effect = self.try_apply_effect(
                            effect,
                            caster,
                            target
                        )

                        if applied_effect is not None:
                            current_result["effects_applied"].append(applied_effect)

            # Passive after_skill handler
            for current_result in random_target_results.values():
                target = current_result["target"]

                if not target.is_alive:
                    continue

                for effect in self.effects:
                    if effect.get("trigger", "after_skill") == "after_skill":

                        applied_effect = self.try_apply_effect(
                            effect,
                            caster,
                            current_result["target"]
                        )

                        if applied_effect is not None:
                            current_result["effects_applied"].append(applied_effect)

            # Hit count threshold
            for current_result in random_target_results.values():
                target = current_result["target"]

                if not target.is_alive:
                    continue
                
                for effect in self.effects:
                    if effect.get("trigger") == "hit_count_threshold":
                        if len(current_result["hit_results"]) >= effect["min_hits"]:

                            applied_effect = self.try_apply_effect(
                                effect,
                                caster,
                                current_result["target"]
                            )

                            if applied_effect is not None:
                                current_result["effects_applied"].append(applied_effect)

            # Special after-skill handlers
            for current_result in random_target_results.values():

                target = current_result["target"]
                target_snapshot = current_result["snapshot"]

                for handler_config in self.after_skill_handlers:
                    handler_name = handler_config["handler"]
                    data = handler_config.get("data", {})

                    handler = AFTER_SKILL_HANDLERS[handler_name]

                    handler(
                        caster,
                        target,
                        self,
                        data,
                        target_snapshot
                    )

            target_results = list(random_target_results.values())

            return SkillResult(
                True,
                target_results=target_results
            )


        #Single enemy or AoE case
        for target in targets:

            target_snapshot = self.get_target_snapshot(target)

            applied_effects = []

            #Damage Phase
            hit_results = []
            total_damage = 0
            any_critical = False

            for hit in range(self.hits):
                hit_multiplier = 1.0

                if self.hit_multipliers:
                    hit_multiplier = self.hit_multipliers[hit]

                damage, critical = self.damage_calc(caster, target, hit_multiplier)
                total_damage += damage

                hit_results.append(
                    {
                        "damage": damage,
                        "critical": critical
                    }
                )

                if critical: 
                    any_critical = True

                broken_effects = target.receive_damage(
                    damage,
                    source=caster
                )

                for broken_effect in broken_effects:

                    if (
                        broken_effect.effect_id == "freeze"
                        and broken_effect.source is not None
                    ):
                        trigger_passives(
                            "freeze_broken_by_damage",
                            broken_effect.source,
                            {
                                "attacker": caster,
                                "target": target,
                                "skill": self,
                                "broken_effect": broken_effect
                            }
                        )

                # Skill on-hit handlers
                for handler_config in self.on_hit_handlers:
                    handler_name = handler_config["handler"]
                    data = handler_config.get("data", {})

                    handler = ON_HIT_HANDLERS[handler_name]

                    handler(
                        caster,
                        target,
                        self,
                        data
                    )

                #Trigger passive on_hit
                context = {
                    "target": target
                }

                trigger_passives(
                    "on_hit",
                    caster,
                    context
                )

                #Per_hit effects
                for effect in self.effects:
                    if effect.get("trigger", "after_skill") == "per_hit":
                        applied_effect = self.try_apply_effect(effect, caster, target)

                        if applied_effect is not None:
                            applied_effects.append(applied_effect)

            #After_skill effects
            for effect in self.effects:
                if effect.get("trigger", "after_skill") == "after_skill":
                    applied_effect = self.try_apply_effect(effect, caster, target)

                    if applied_effect is not None:
                        applied_effects.append(applied_effect)

            #Hit count threshold
            for effect in self.effects:
                if effect.get("trigger") == "hit_count_threshold":
                    if self.hits >= effect["min_hits"]:
                        applied_effect = self.try_apply_effect(effect, caster, target)

                        if applied_effect is not None:
                            applied_effects.append(applied_effect)

            # Special after-skill handlers
            for handler_config in self.after_skill_handlers:
                handler_name = handler_config["handler"]
                data = handler_config.get("data", {})

                handler = AFTER_SKILL_HANDLERS[handler_name]

                handler(
                    caster,
                    target,
                    self,
                    data,
                    target_snapshot
                )

            target_result = {
                "target": target,
                "total_damage": total_damage,
                "any_critical": any_critical,
                "hit_results": hit_results,
                "effects_applied": applied_effects
            }

            target_results.append(target_result)

        skill_result = SkillResult(success=True, target_results=target_results)

        return skill_result


    def try_apply_effect(self, effect, caster, target):

        # CONDITION
        condition = effect.get("condition")

        if condition is not None:
            condition_type = condition["type"]
            condition_checker = EFFECT_CONDITIONS[condition_type]

            condition_met = condition_checker(
                caster,
                target,
                self,
                condition
            )

            if not condition_met:
                return None

        #SKILL PROC CHANCE        
        trigger_chance = random.random()

        if trigger_chance > effect["chance"]:
            return None
    
        effect_data = STATUS_EFFECT_DATA[effect["effect_id"]]

        # ACCURACY / RESISTANCE
        if (
            effect_data["effect_type"] == EffectType.DEBUFF
            and not effect.get("ignore_resistance", False)
        ):
            accuracy = caster.get_effective_stat("accuracy")
            resistance = target.get_effective_stat("resistance")

            resist_chance = max(15, resistance - accuracy)

            resist_chance = min(100, resist_chance)

            resist_roll = random.uniform(0, 100)

            if resist_roll < resist_chance:
                return None

        status_effect = StatusEffect(
            effect_id=effect["effect_id"],
            name=effect_data["name"],
            stat=effect_data["stat"],
            effect_type=effect_data["effect_type"],
            modifier=effect_data["modifier"],
            duration=effect["turns"],
            stacks=effect.get("stacks", 1),
            max_stacks=effect_data.get("max_stacks", 1),
            source=caster,
            modifier_mode=effect_data.get("modifier_mode", "multiplicative")
        )

        if effect_data["effect_type"] == EffectType.BUFF:
            applied_effect = caster.apply_status_effect(status_effect)

        elif effect_data["effect_type"] == EffectType.DEBUFF:
            applied_effect = target.apply_status_effect(status_effect)

        return applied_effect


    def get_target_snapshot(self, target):
        debuffs = {}

        for debuff in target.debuffs:
            debuffs[debuff.effect_id] = {
                "stacks": debuff.stacks,
                "remaining_turns": debuff.remaining_turns
            }

        return {
            "debuffs": debuffs
        }



class HealingSkill(Skill):
    def __init__(self, skill_id, name, scaling_stat, base_scaling_ratio, target_type, scaling_bonus=0, cooldown=0):
        super().__init__(skill_id, name, target_type, cooldown)
        self.skill_type = SkillType.HEALING
        self.scaling_stat = scaling_stat
        self.base_scaling_ratio = base_scaling_ratio
        self.scaling_bonus = scaling_bonus


    @property
    def scaling_ratio(self):
        return self.base_scaling_ratio + self.scaling_bonus 


    def healing(self, caster, target):
        stat_value = getattr(caster, self.scaling_stat)
        heal_value = int(self.scaling_ratio * stat_value)

        return target.heal(heal_value)


    def execute(self, caster, targets):
        target_results = []

        for target in targets:
            heal_value = self.healing(caster, target)

            target_results.append(
                {
                    "target": target,
                    "heal_value": heal_value
                }
            )

        return SkillResult(
            True,
            target_results=target_results
        )



class PassiveSkill(Skill):
    def __init__(self, skill_id, name, trigger=None, handler=None):
        super().__init__(skill_id, name)
        self.trigger = trigger
        self.handler = handler
        self.skill_type = SkillType.PASSIVE


    def activate(self, owner, context):
        if self.handler is None:
            return

        handler = PASSIVE_HANDLERS[self.handler]
        handler(owner, context, self)
            


class SkillResult():
    def __init__(self, success, value=0, critical=False, effects_applied=None, hit_results=None, target_results=None):
        self.success = success
        self.value = value
        self.critical = critical
        self.effects_applied = effects_applied if effects_applied is not None else []
        self.hit_results = hit_results if hit_results is not None else []
        self.target_results = target_results if target_results is not None else []

