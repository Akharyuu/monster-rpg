import random

from .enums import SkillType, EffectType, TargetType
from ..data.status_effect_data import STATUS_EFFECT_DATA
from ..factories.status_effect_factory import create_status_effect

from ..combat.passive_handlers import PASSIVE_HANDLERS
from ..combat.passive_triggers import trigger_passives
from ..combat.skill_damage_handlers import DAMAGE_HANDLERS
from ..combat.skill_after_handlers import AFTER_SKILL_HANDLERS
from ..combat.skill_on_hit_handlers import ON_HIT_HANDLERS
from ..combat.skill_effect_conditions import EFFECT_CONDITIONS
from ..combat.skill_after_use_handlers import AFTER_USE_HANDLERS


class Skill:

    # =========================================================
    #                       INITIALIZATION
    # =========================================================

    def __init__(self, skill_id, name, target_type=None, cooldown=0):
        self.skill_id = skill_id
        self.name = name
        self.target_type = target_type
        self.cooldown = cooldown
        self.current_cooldown = 0


    # =========================================================
    #                        COOLDOWN
    # =========================================================

    def is_available(self):
        return self.current_cooldown == 0



    def trigger_cooldown(self):
        self.current_cooldown = self.cooldown



    def reduce_cooldown(self):

        if self.current_cooldown > 0:
            self.current_cooldown -= 1



    def reset_cooldown(self):
        self.current_cooldown = 0


    # =========================================================
    #                  PYTHON SPECIAL METHODS
    # =========================================================

    def __eq__(self, other):
        return isinstance(other, Skill) and self.skill_id == other.skill_id



    def __repr__(self):
        return (
            f"Skill("
            f"name='{self.name}', "
            f"cooldown={self.cooldown}"
            f")"
        )





class DamageSkill(Skill):

    # =========================================================
    #                       INITIALIZATION
    # =========================================================

    def __init__(self, skill_id, name, multiplier, hits, hit_multipliers, target_type, scaling_stat="attack", cooldown=0, 
                 damage_handler=None, damage_handler_data=None, on_hit_handlers=None, after_skill_handlers=None, after_use_handlers=None,
                 effects=None):
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

        self.after_use_handlers = (
            after_use_handlers
            if after_use_handlers is not None
            else []
        )

        self.effects = (
            effects
            if effects is not None
            else []
        )


    # =========================================================
    #                    DAMAGE CALCULATION
    # =========================================================

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
                critical_damage_bonus += attacker.get_effective_stat("crit_damage") / 100
                critical = True

            #Final damage
            final_damage = raw_damage * damage_reduction * attribute_modifier * critical_damage_bonus

            return max(1, int(final_damage)), critical


# =========================================================
#                        EXECUTION
# =========================================================

    def execute(self, caster, targets, context=None):
            
        if context is None:
            context = {}
    
        target_results = []

        # RANDOM_ENEMIES can choose a different living target on every hit.
        # If all enemies die before the skill ends, the remaining hits keep
        # targeting the last monster hit, but only as visual overkill hits.

        if self.target_type == TargetType.RANDOM_ENEMIES:

            random_target_results = {}
            last_target = None

            for hit in range(self.hits):

                # Recalculate living targets before every hit so a dead
                # monster cannot be selected again.
                alive_targets = [
                    target
                    for target in targets
                    if target.is_alive
                ]

                if alive_targets:
                    target = random.choice(alive_targets)
                    last_target = target
                    gameplay_active = True

                else:
                    # No living targets remain, but the skill animation
                    # still has hits left to resolve.
                    if last_target is None:
                        break

                    target = last_target
                    gameplay_active = False

                # Create one accumulated result per target.
                if target not in random_target_results:
                    random_target_results[target] = (
                        self.create_target_result(target)
                    )

                current_result = random_target_results[target]

                self.resolve_hit(
                    caster,
                    target,
                    hit,
                    current_result,
                    gameplay_active=gameplay_active
                )

            # Resolve effects that happen after all hits against each target.
            for current_result in random_target_results.values():

                self.resolve_after_skill_for_target(
                    caster,
                    current_result
                )

            target_results = list(
                random_target_results.values()
            )

            skill_result = SkillResult(
                success=True,
                target_results=target_results
            )

            self.resolve_after_use(
                caster,
                skill_result,
                context
            )

            return skill_result


        # SINGLE_ENEMY and ALL_ENEMIES:
        # every configured hit continues visually even if the target dies
        # before the skill animation has finished.
        for target in targets:

            target_result = self.create_target_result(
                target
            )

            # Resolve every hit through the shared hit pipeline.
            for hit in range(self.hits):

                # Once this target is dead, remaining hits are visual only.
                gameplay_active = target.is_alive

                self.resolve_hit(
                    caster,
                    target,
                    hit,
                    target_result,
                    gameplay_active=gameplay_active
                )

            self.resolve_after_skill_for_target(
                caster, 
                target_result
            )

            target_results.append(target_result)

        skill_result = SkillResult(
            success=True,
            target_results=target_results
        )

        self.resolve_after_use(
            caster,
            skill_result,
            context
        )

        return skill_result


# =========================================================
#                     STATUS EFFECTS
# =========================================================

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

        status_effect = create_status_effect(
            effect_id=effect["effect_id"],
            duration=effect["turns"],
            stacks=effect.get("stacks", 1),
            source=caster
        )

        if effect_data["effect_type"] == EffectType.BUFF:
            applied_effect = caster.apply_status_effect(status_effect)

        elif effect_data["effect_type"] == EffectType.DEBUFF:
            applied_effect = target.apply_status_effect(status_effect)

        return applied_effect


# =========================================================
#                       TARGET STATE
# =========================================================

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



    def create_target_result(self, target):
        # Creates the result container used while resolving damage against one target.
        # The snapshot stores the target state before this skill starts affecting it.

        return {
            "target": target,
            "total_damage": 0,
            "any_critical": False,
            "hit_results": [],
            "effects_applied": [],
            "snapshot": self.get_target_snapshot(target)
        }


# =========================================================
#                      HIT RESOLUTION
# =========================================================

    def resolve_hit(self, caster, target, hit_index, target_result, gameplay_active=True):
    
        # Resolves one complete hit against one target.
        # This centralizes all mechanics that must happen every time a hit lands,
        # regardless of the skill target type.

        # If gameplay_active is False, the hit is still calculated and stored
        # for the visual flow of the skill, but it cannot modify combat state
        # or trigger gameplay mechanics.

        # Some skills can give individual hits a different damage multiplier.
        hit_multiplier = 1.0

        if self.hit_multipliers:
            hit_multiplier = self.hit_multipliers[hit_index]

        damage, critical = self.damage_calc(
            caster,
            target,
            hit_multiplier
        )

        # Always record the hit so the full skill sequence can be displayed,
        # even when the target was already defeated.
        target_result["total_damage"] += damage

        target_result["hit_results"].append(
            {
                "damage": damage,
                "critical": critical
            }
        )

        if critical:
            target_result["any_critical"] = True

        # Overkill hits are visual only.
        # They do not change HP, trigger passives or apply combat effects.
        if not gameplay_active:
            return

        # Direct damage can break effects such as Freeze.
        broken_effects = target.receive_damage(
            damage,
            source=caster
        )

        # A broken Freeze can trigger passives belonging to the monster
        # that originally applied that Freeze.
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

        # Skill-specific mechanics that happen immediately after each hit.
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

        # Passives belonging to the attacker that react to landing a hit.
        trigger_passives(
            "on_hit",
            caster,
            {
                "target": target
            }
        )

        # Dead targets can still receive the remaining hits of the skill,
        # but they cannot receive new status effects.
        if target.is_alive:

            for effect in self.effects:

                if effect.get("trigger", "after_skill") == "per_hit":

                    applied_effect = self.try_apply_effect(
                        effect,
                        caster,
                        target
                    )

                    if applied_effect is not None:
                        target_result["effects_applied"].append(
                            applied_effect
                        )


# =========================================================
#                  AFTER TARGET RESOLUTION
# =========================================================

    def resolve_after_skill_for_target(self, caster, target_result):

        # Resolves mechanics that happen after all hits against one target.

        # Status effects are only attempted if the target survived.
        # Special after-skill handlers always run because they may depend
        # on the target's pre-skill state even when the target was defeated.

        target = target_result["target"]

        # Dead targets cannot receive new status effects.
        if target.is_alive:

            # Effects attempted once after the full skill.
            for effect in self.effects:

                if (
                    effect.get("trigger", "after_skill")
                    == "after_skill"
                ):
                    applied_effect = self.try_apply_effect(
                        effect,
                        caster,
                        target
                    )

                    if applied_effect is not None:
                        target_result["effects_applied"].append(
                            applied_effect
                        )

            # Effects that require this target to have received
            # a minimum number of hits.
            for effect in self.effects:

                if effect.get("trigger") == "hit_count_threshold":

                    hits_received = len(
                        target_result["hit_results"]
                    )

                    if hits_received >= effect["min_hits"]:

                        applied_effect = self.try_apply_effect(
                            effect,
                            caster,
                            target
                        )

                        if applied_effect is not None:
                            target_result[
                                "effects_applied"
                            ].append(applied_effect)

        # Special handlers can still matter after killing the target.
        for handler_config in self.after_skill_handlers:

            handler_name = handler_config["handler"]
            data = handler_config.get("data", {})

            handler = AFTER_SKILL_HANDLERS[
                handler_name
            ]

            handler(
                caster,
                target,
                self,
                data,
                target_result["snapshot"]
            )


# =========================================================
#                   AFTER USE RESOLUTION
# =========================================================

    def resolve_after_use(self, caster, skill_result, context):

        for handler_config in self.after_use_handlers:

            handler_name = handler_config["handler"]
            data = handler_config.get("data", {})

            handler = AFTER_USE_HANDLERS[
                handler_name
            ]

            result = handler(
                caster,
                self,
                data,
                context,
                skill_result
            )

            if result is not None:
                skill_result.events.append(result)





class HealingSkill(Skill):

    # =========================================================
    #                       INITIALIZATION
    # =========================================================

    def __init__(self, skill_id, name, scaling_stat, base_scaling_ratio, target_type, scaling_bonus=0, cooldown=0):
        super().__init__(skill_id, name, target_type, cooldown)

        self.skill_type = SkillType.HEALING
        self.scaling_stat = scaling_stat
        self.base_scaling_ratio = base_scaling_ratio
        self.scaling_bonus = scaling_bonus


    # =========================================================
    #                         HEALING
    # =========================================================

    @property
    def scaling_ratio(self):
        return (
            self.base_scaling_ratio
            + self.scaling_bonus
        )



    def healing(self, caster, target):

        stat_value = caster.get_effective_stat(
            self.scaling_stat
        )

        heal_value = int(
            self.scaling_ratio
            * stat_value
        )

        return target.heal(
            heal_value
        )


    # =========================================================
    #                        EXECUTION
    # =========================================================

    def execute(self, caster, targets, context=None):

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
            success=True,
            target_results=target_results
        )





class PassiveSkill(Skill):

    # =========================================================
    #                       INITIALIZATION
    # =========================================================

    def __init__(self, skill_id, name, trigger=None, handler=None):
        super().__init__(skill_id, name)

        self.trigger = trigger
        self.handler = handler
        self.skill_type = SkillType.PASSIVE


    # =========================================================
    #                       ACTIVATION
    # =========================================================

    def activate(self, owner, context):

        if self.handler is None:
            return

        handler = PASSIVE_HANDLERS[self.handler]
        handler(owner, context, self)
            


class SkillResult():

    # =========================================================
    #                       INITIALIZATION
    # =========================================================

    def __init__(self, success, value=0, critical=False, effects_applied=None, hit_results=None, target_results=None, events=None):
        self.success = success
        self.value = value
        self.critical = critical
        
        self.effects_applied = effects_applied if effects_applied is not None else []
        self.hit_results = hit_results if hit_results is not None else []
        self.target_results = target_results if target_results is not None else []
        self.events = events if events is not None else []

