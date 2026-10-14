from .enums import Attribute, EffectType

from .skills import SkillResult

from ..combat.passive_triggers import trigger_passives
from ..combat.passive_modifiers import get_passive_stat_bonus
from ..combat.telemetry import record_telemetry

from ..data.passive_data import PASSIVE_DATA
from ..data.glyph_stat_data import GLYPH_STAT_MAP
from ..data.glyph_set_data import GLYPH_SET_DATA
from ..data.experience_data import XP_TO_NEXT_LEVEL, BASE_EXP_YIELD, RARITY_EXP_MULTIPLIER
from ..data.monster_data import MONSTER_DATA
from ..data.stat_growth_data import LEVEL_STAT_MULTIPLIER, ASCENDED_STAT_MULTIPLIER
from ..data.status_effect_data import STATUS_EFFECT_DATA


class Monster:

    # =========================================================
    #                       INITIALIZATION
    # =========================================================

    def __init__(self, instance_id, monster_id, name, family, attribute, rarity, health, max_health, attack, defense, speed, 
                 skills=None, passives=None, level=1, level_limit=10, experience=0, ascended=False, combat_resources=None):

        #Attributes
        self.instance_id = instance_id
        self.monster_id = monster_id
        self.name = name
        self.family = family
        self.attribute = attribute
        self.rarity = rarity
        self.level = level
        self.level_limit = level_limit
        self.experience = experience
        self.ascended = ascended
        self.action_gauge = 0
        self.resonance = 0
        self.extra_turn_pending = False
        self.forced_turn_pending = False
        self._preserve_action_gauge_forced_turn = False
        self.banished = False
        self.special_states = {}
        self.internal_cooldowns = {}
        self.death_order = None
        self._death_recorded = False
        self._battle_state = None
        self._combat_team = []
        self._combat_opponents = []

        if combat_resources is None:
            self.combat_resources = {}
        else:
            self.combat_resources = combat_resources

        #Stats
        self.max_health = max_health
        self.health = health
        self.attack = attack
        self.defense = defense
        self.speed = speed

        self.accuracy = 25
        self.resistance = 25
        
        self.crit_rate = 15
        self.crit_damage = 50

        #Skills / Passives
        if skills is None:
            self.skills = []
        else:
            self.skills = skills

        if passives is None:
            self.passives = []
        else:
            self.passives = passives

        #Glyphs
        self.glyphs = {
            1: None,
            2: None,
            3: None,
            4: None,
            5: None
        }

        #Buffs / Debuffs
        self.buffs = []
        self.debuffs = []


    # =========================================================
    #                      BASIC PROPERTIES
    # =========================================================

    @property
    def display_name(self):
        if self.ascended:
            return self.name

        return f"{self.attribute.value} {self.family}"


    @property
    def health(self):
        return self._health


    @health.setter
    def health(self, value):
        if value < 0:
            value = 0
        elif value > self.max_health:
            value = self.max_health

        self._health = value


    @property
    def is_alive(self):
        return self.health > 0


    # =========================================================
    #                  COMBAT STATE PROPERTIES
    # =========================================================

    @property
    def is_stunned(self):
        for debuff in self.debuffs:
            if debuff.effect_id == "stun":
                return True

        return False


    @property
    def is_frozen(self):
        for debuff in self.debuffs:
            if debuff.effect_id == "freeze":
                return True

        return False


    @property
    def is_silenced(self):

        if self.is_headless:
            return False

        for debuff in self.debuffs:
            if debuff.effect_id == "silence":
                return True

        return False


    @property
    def has_immunity(self):
        for buff in self.buffs:
            if buff.effect_id == "immunity":
                return True

        return False


    @property
    def has_invincibility(self):
        for buff in self.buffs:
            if buff.effect_id == "invincibility":
                return True

        return False


    @property
    def has_oblivion(self):
        for debuff in self.debuffs:
            if debuff.effect_id == "oblivion":
                return True

        return False


    @property
    def has_heal_block(self):

        return any(
            debuff.effect_id == "heal_block"
            for debuff in self.debuffs
        )


    @property
    def is_headless(self):

        return self.special_states.get(
            "headless",
            False
        )


    @property
    def cannot_act(self):
        return self.is_stunned or self.is_frozen


    # =========================================================
    #                          STATS
    # =========================================================

    def update_level_stats(self):

        data = MONSTER_DATA[self.monster_id]

        if self.ascended:
            multiplier = ASCENDED_STAT_MULTIPLIER[self.level]
        else:
            multiplier = LEVEL_STAT_MULTIPLIER[self.level]

        self.max_health = round(data["max_health"] * multiplier)
        self.attack = round(data["attack"] * multiplier)
        self.defense = round(data["defense"] * multiplier)
        self.speed = round(data["speed"] * multiplier)
        self.health = self.max_health



    def get_equipped_stat(self, stat):

        if stat == "health":
            base_stat = self.max_health
        else:
            base_stat = getattr(self, stat)

        flat = GLYPH_STAT_MAP[stat]["flat"]
        flat_bonus = 0

        percent = GLYPH_STAT_MAP[stat].get("percent")
        percent_bonus = 0

        for glyph in self.glyphs.values():

            if glyph is None:
                continue

            if glyph.main_stat == flat:
                flat_bonus += glyph.main_value

            elif glyph.main_stat == percent:
                percent_bonus += glyph.main_value
                
            for sub_stat in glyph.sub_stats:
                if sub_stat.stat == flat:
                    flat_bonus += sub_stat.total_value

                elif sub_stat.stat == percent:
                    percent_bonus += sub_stat.total_value

        active_set_bonus = self.get_active_sets()

        for set_id, quantity in active_set_bonus.items():

            set_data = GLYPH_SET_DATA[set_id]
            effects = set_data.get("effects", {})

            if flat in effects:
                flat_bonus += effects[flat] * quantity

            if percent and percent in effects:
                percent_bonus += effects[percent] * quantity

        if percent:
            return base_stat * (1 + percent_bonus / 100) + flat_bonus

        return base_stat + flat_bonus
    

                
    def get_effective_stat(self, stat):

        multiplicative_modifier = 1
        additive_modifier = 0

        for buff in self.buffs:
            if stat == buff.stat:
                if buff.modifier_mode == "additive":
                    additive_modifier += buff.modifier
                else:
                    multiplicative_modifier *= buff.modifier

        for debuff in self.debuffs:
            if stat == debuff.stat:
                if debuff.modifier_mode == "additive":
                    additive_modifier += debuff.modifier
                else:
                    multiplicative_modifier *= debuff.modifier

        base = self.get_equipped_stat(stat)

        effective_stat = ( base * multiplicative_modifier + additive_modifier )
        effective_stat += get_passive_stat_bonus(self, stat)

        return effective_stat



    def get_healing_hp(self):

        base_max_health = self.max_health

        equipped_max_health = self.get_equipped_stat("health")

        bonus_max_health = ( equipped_max_health - base_max_health )

        healing_hp = ( base_max_health + bonus_max_health * 0.50 )

        return healing_hp



    def get_attribute_modifier(self, defender):

        neutral_all_attributes = (
            getattr(
                self,
                "_neutral_all_attributes",
                False
            )
            or getattr(
                defender,
                "_neutral_all_attributes",
                False
            )
        )

        if neutral_all_attributes:
            return 1

        neutral_core_attributes = (
            getattr(
                self,
                "_neutral_core_attributes",
                False
            )
            or getattr(
                defender,
                "_neutral_core_attributes",
                False
            )
        )

        both_primary = (
            getattr(
                self,
                "_balance_primary",
                False
            )
            and getattr(
                defender,
                "_balance_primary",
                False
            )
        )

        if (
            neutral_core_attributes
            and not both_primary
        ):
            return 1

        if (
            (
                self.attribute == Attribute.IGNEOUS
                and defender.attribute
                == Attribute.ABYSSAL
            )
            or (
                self.attribute == Attribute.ABYSSAL
                and defender.attribute
                == Attribute.STORM
            )
            or (
                self.attribute == Attribute.STORM
                and defender.attribute
                == Attribute.IGNEOUS
            )
        ):
            return 0.85

        elif (
            (
                self.attribute == Attribute.IGNEOUS
                and defender.attribute
                == Attribute.STORM
            )
            or (
                self.attribute == Attribute.ABYSSAL
                and defender.attribute
                == Attribute.IGNEOUS
            )
            or (
                self.attribute == Attribute.STORM
                and defender.attribute
                == Attribute.ABYSSAL
            )
        ):
            return 1.15

        return 1


    # =========================================================
    #                        LEVEL & EXP
    # =========================================================

    def gain_exp(self, exp):

        if self.level >= self.level_limit:
            return

        while exp > 0:

            required_exp_to_level_up = (XP_TO_NEXT_LEVEL[self.level] - self.experience)

            if exp >= required_exp_to_level_up:

                exp -= required_exp_to_level_up
                self.level_up()

                if self.level >= self.level_limit:
                    break

            else:
                self.experience += exp
                break



    def level_up(self):
        self.level += 1
        self.experience = 0
        self.update_level_stats()



    def get_exp_yield(self):

        base_exp = BASE_EXP_YIELD[self.level]
        rarity_multiplier = RARITY_EXP_MULTIPLIER[self.rarity]

        return round(base_exp * rarity_multiplier)
           

    # =========================================================
    #                          GLYPHS
    # =========================================================

    def equip_glyph(self, glyph):
        old_glyph = self.glyphs[glyph.slot_id]

        self.glyphs[glyph.slot_id] = glyph

        return old_glyph



    def unequip_glyph(self, slot):
        glyph = self.glyphs[slot]

        self.glyphs[slot] = None

        return glyph



    def get_active_sets(self):
        sets = {}
        active_sets = {}

        for glyph in self.glyphs.values():
            if glyph is None:
                continue

            sets[glyph.set_id] = sets.get(glyph.set_id, 0) + 1

        for set_id, quantity in sets.items():
            if quantity >= GLYPH_SET_DATA[set_id]["pieces_required"]:
                active_sets[set_id] = quantity // GLYPH_SET_DATA[set_id]["pieces_required"]

        return active_sets


    # =========================================================
    #                   SKILLS & PASSIVES
    # =========================================================

    def get_skill(self, index):
        if index not in range(1, len(self.skills) + 1):
            return None

        return self.skills[index -1]


    
    def use_skill(self, targets, skill, combat_context=None):

        if skill not in self.skills:
            print(f"{self.name} no conoce la habilidad {skill.name}.")
            return SkillResult(False, None)

        if not skill.is_available():
            print(f"The skill is currently on cooldown. {skill.current_cooldown} turns left.")
            return SkillResult(False, None)
        
        # Shared context for this specific skill execution.
        context = {
            "skill": skill,
            "targets": targets
        }

        if combat_context is not None:
            context.update(combat_context)

        skill_use_metrics = {
            "null_rend": "null_rend_uses",
            "null_rend_obliterate": "null_rend_uses",
            "null_rend_annihilation": "null_rend_uses",
            "dismantle": "dismantle_uses",
            "dismantle_decimation": "dismantle_uses"
        }

        skill_use_metric = skill_use_metrics.get(
            skill.skill_id
        )

        if skill_use_metric is not None:
            record_telemetry(
                context.get("telemetry"),
                self,
                skill_use_metric,
                1
            )

        # Passives that activate before the skill.
        trigger_passives(
            "before_skill",
            self,
            context
        )

        skill_result = skill.execute(
            self,
            targets,
            context
        )

        # Add the result so after_skill passives can inspect what happened.
        context["skill_result"] = skill_result

        skill.trigger_cooldown()

        # Passives that activate after the skill.
        trigger_passives(
            "after_skill",
            self,
            context
        )

        return skill_result



    def reduce_skill_cooldowns(self):
        for skill in self.skills:
            skill.reduce_cooldown()



    def has_passive_trait(self, trait):

        if self.has_oblivion:
            return False

        for passive in self.passives:
            data = PASSIVE_DATA[passive.skill_id]

            if trait in data.get("traits", []):
                return True

        return False


    # =========================================================
    #                     HEALTH & DAMAGE
    # =========================================================

    def receive_damage(self, damage, source=None, telemetry=None):

        if self.has_invincibility:
            return []

        # If monster has Shield, the shield absorbs damage
        shield = None

        for buff in self.buffs:

            if buff.effect_id == "shield":
                shield = buff
                break

        if shield is not None:

            absorbed_damage = min(
                damage,
                shield.value
            )

            shield.value -= absorbed_damage
            damage -= absorbed_damage

            record_telemetry(
                telemetry,
                shield.source,
                "shield_absorbed",
                absorbed_damage
            )

            if shield.value <= 0:
                self.buffs.remove(shield)

        # When Shield is consumed // Monster has no Shield: process damage normally
        deathless_passive = None

        if (
            self.is_headless
            and not self.has_oblivion
            and self.get_internal_cooldown(
                "deathless_rider"
            ) == 0
        ):

            for passive in self.passives:

                if (
                    passive.handler
                    == "deathless_rider"
                ):
                    deathless_passive = passive
                    break

        deathless_active = (
            deathless_passive is not None
        )

        already_triggered = (
            self.special_states.get(
                "deathless_triggered_this_skill",
                False
            )
        )

        lethal_damage = (
            self.health - damage
            <= 0
        )

        if (
            deathless_active
            and (
                lethal_damage
                or already_triggered
            )
        ):
            self.special_states[
                "deathless_triggered_this_skill"
            ] = True

            self.health = max(
                1,
                self.health - damage
            )

        else:
            self.health -= damage

        broken_effects = []

        preserve_freeze_from_attacker = (
            source is not None
            and source.has_passive_trait(
                "preserve_freeze_on_hit"
            )
        )

        new_debuffs = []

        for debuff in self.debuffs:

            preserve_freeze_from_source = (
                debuff.effect_id == "freeze"
                and debuff.source is not None
                and debuff.source.has_passive_trait(
                    "preserve_applied_freeze_on_damage"
                )
            )

            preserve_freeze = (
                preserve_freeze_from_attacker
                or preserve_freeze_from_source
            )

            if (
                debuff.effect_id == "freeze"
                and not preserve_freeze
            ):
                broken_effects.append(debuff)
                continue

            new_debuffs.append(debuff)

        self.debuffs = new_debuffs

        return broken_effects



    def finalize_after_enemy_skill(self):

        if not self.special_states.pop(
            "deathless_triggered_this_skill",
            False
        ):
            return

        passive = next(
            (
                passive
                for passive in self.passives
                if passive.handler
                == "deathless_rider"
            ),
            None
        )

        if passive is None:
            return

        self.clear_named_target()
        self.reset_debuffs()

        self.set_internal_cooldown(
            "deathless_rider",
            passive.handler_data.get(
                "internal_cooldown",
                6
            )
        )


    def heal(self, value):

        if not self.is_alive:
            return 0

        if self.has_heal_block:
            return 0

        hp_ratio_before = (
            self.health
            / self.max_health
        )

        healing_multiplier = 1.0

        for opponent in getattr(
            self,
            "_combat_opponents",
            []
        ):

            if not opponent.is_alive:
                continue

            if opponent.has_oblivion:
                continue

            for passive in opponent.passives:

                if (
                    passive.handler
                    != "final_omen"
                ):
                    continue

                data = passive.handler_data

                if (
                    hp_ratio_before
                    >= data["hp_threshold"]
                ):
                    continue

                healing_multiplier *= (
                    data.get(
                        "healing_received_multiplier",
                        1
                    )
                )

        value = int(
            value
            * healing_multiplier
        )

        base_health = self.health
        self.health += value

        actual_heal = (
            self.health
            - base_health
        )

        if actual_heal <= 0:
            return 0

        for opponent in getattr(
            self,
            "_combat_opponents",
            []
        ):

            if not opponent.is_alive:
                continue

            trigger_passives(
                "on_enemy_healed",
                opponent,
                {
                    "target": self,
                    "healing": actual_heal,
                    "hp_ratio_before":
                        hp_ratio_before
                }
            )

        return actual_heal



    def reset_health(self):
        self.health = self.max_health


    # =========================================================
    #                      STATUS EFFECTS
    # =========================================================

    def apply_status_effect(
        self,
        effect,
        telemetry=None
    ):

        if effect.effect_type == EffectType.BUFF:
            effects_list = self.buffs

        elif effect.effect_type == EffectType.DEBUFF:

            if (
                effect.effect_id == "silence"
                and self.is_headless
            ):
                return None

            if self.has_immunity:
                return None

            effects_list = self.debuffs

        else:
            return None

        for active_effect in effects_list:
            if active_effect.effect_id == effect.effect_id:

                if active_effect.effect_id == "shield":

                    if effect.value > active_effect.value:
                        active_effect.value = effect.value

                if active_effect.effect_id in ("burn", "poison"):
                    active_effect.stacks += effect.stacks

                    if active_effect.stacks > active_effect.max_stacks:
                        active_effect.stacks = active_effect.max_stacks

                if effect.duration > active_effect.remaining_turns:
                    active_effect.remaining_turns = effect.duration

                # Update who applied/refreshed the effect.
                active_effect.source = effect.source

                if (
                    effect.effect_type == EffectType.BUFF
                    and effect.source is not None
                ):
                    trigger_passives(
                        "on_apply_buff",
                        effect.source,
                        {
                            "target": self,
                            "effect": active_effect,
                            "telemetry": telemetry
                        }
                    )

                return active_effect

        if len(effects_list) < 5:
            effects_list.append(effect)

            if (
                effect.effect_type == EffectType.BUFF
                and effect.source is not None
            ):
                trigger_passives(
                    "on_apply_buff",
                    effect.source,
                    {
                        "target": self,
                        "effect": effect,
                        "telemetry": telemetry
                    }
                )

            return effect

        return None



    def reduce_remaining_turns(self, effects_at_turn_start):

        #Buffs
        for buff in self.buffs:
            if id(buff) in effects_at_turn_start:
                buff.reduce_remaining_turns()

        active_buffs = []

        for buff in self.buffs:
            if buff.is_active:
                active_buffs.append(buff)

        self.buffs = active_buffs        

        #Debuffs
        for debuff in self.debuffs:
            if id(debuff) in effects_at_turn_start:
                debuff.reduce_remaining_turns()

        active_debuffs = []

        for debuff in self.debuffs:
            if debuff.is_active:
                active_debuffs.append(debuff)

        self.debuffs = active_debuffs   



    def apply_damage_over_time(self, telemetry=None):
        total_damage = 0

        if self.has_invincibility:
            return

        for debuff in self.debuffs:

            damage = 0

            if debuff.effect_id == "burn":

                if debuff.stacks == 1:
                    damage = self.max_health * 0.03
                elif debuff.stacks == 2:
                    damage = self.max_health * 0.06
                elif debuff.stacks == 3:
                    damage = self.max_health * 0.1

            elif debuff.effect_id == "poison":
                damage = (
                    self.max_health
                    * 0.05
                    * debuff.stacks
                )

            damage = int(damage)

            if damage <= 0:
                continue

            health_before = self.health

            self.health -= damage

            actual_damage = (
                health_before - self.health
            )

            total_damage += actual_damage

            record_telemetry(
                telemetry,
                debuff.source,
                "dot_damage",
                actual_damage
            )

        if total_damage > 0:
            print(
                f"{self.display_name} takes "
                f"{total_damage} damage from DoT."
            )
            print()



    def apply_healing_over_time(self, telemetry=None):

        total_healing = 0

        for buff in self.buffs:

            if buff.effect_id == "regrowth":

                data = STATUS_EFFECT_DATA[buff.effect_id]

                heal_amount = int( self.max_health * data["heal_ratio"] )

                actual_heal = self.heal(heal_amount)

                total_healing += actual_heal

                record_telemetry(
                    telemetry,
                    buff.source,
                    "healing",
                    actual_heal
                )

        if total_healing > 0:

            print(
                f"{self.display_name} "
                f"recovers {total_healing} HP "
                f"from Regrowth."
            )



    def reset_buffs(self):
        self.buffs = []



    def reset_debuffs(self):
        self.debuffs = []


    # =========================================================
    #                    SPECIAL COMBAT STATES
    # =========================================================

    def apply_named(
        self,
        target,
        turns=2
    ):

        self.clear_named_target()

        self.special_states[
            "named_target"
        ] = target

        self.special_states[
            "headless"
        ] = True

        target.special_states[
            "named_by"
        ] = self

        target.special_states[
            "named_remaining_turns"
        ] = turns


    def clear_named_target(self):

        target = self.special_states.get(
            "named_target"
        )

        if target is not None:

            if (
                target.special_states.get(
                    "named_by"
                )
                is self
            ):
                target.special_states.pop(
                    "named_by",
                    None
                )
                target.special_states.pop(
                    "named_remaining_turns",
                    None
                )

        self.special_states.pop(
            "named_target",
            None
        )

        self.special_states.pop(
            "headless",
            None
        )


    def reduce_special_state_turns(self):

        named_by = self.special_states.get(
            "named_by"
        )

        if named_by is None:
            return

        remaining = (
            self.special_states.get(
                "named_remaining_turns",
                0
            )
            - 1
        )

        self.special_states[
            "named_remaining_turns"
        ] = remaining

        if remaining <= 0:

            if (
                named_by.special_states.get(
                    "named_target"
                )
                is self
            ):
                named_by.clear_named_target()


    def reduce_internal_cooldowns(self):

        for cooldown_id in list(
            self.internal_cooldowns
        ):

            value = self.internal_cooldowns[
                cooldown_id
            ]

            if value > 0:
                value -= 1

            self.internal_cooldowns[
                cooldown_id
            ] = value


    def get_internal_cooldown(
        self,
        cooldown_id
    ):

        return self.internal_cooldowns.get(
            cooldown_id,
            0
        )


    def set_internal_cooldown(
        self,
        cooldown_id,
        turns
    ):

        self.internal_cooldowns[
            cooldown_id
        ] = turns


    # =========================================================
    #                       ACTION GAUGE
    # =========================================================

    def increase_action_gauge(self, amount):
        self.action_gauge += amount

        if self.action_gauge > 1:
            self.action_gauge = 1



    def reduce_action_gauge(self, amount):
        self.action_gauge -= amount

        if self.action_gauge < 0:
            self.action_gauge = 0



    def reset_action_gauge(self):
        self.action_gauge = 0


    # =========================================================
    #                   COMBAT RESOURCES
    # =========================================================

    def add_combat_resource(self, name, value, max_value):
        if name in self.combat_resources:
            self.combat_resources[name] += value
        else:
            self.combat_resources[name] = value

        if self.combat_resources[name] > max_value:
            self.combat_resources[name] = max_value



    def get_combat_resource(self, name):
        if name in self.combat_resources:
            return self.combat_resources[name]

        return 0



    def consume_combat_resource(self, name, value):
        if name in self.combat_resources and self.combat_resources[name] >= value:
            self.combat_resources[name] -= value
            return True
        
        return False



    def reset_combat_resources(self):
        self.combat_resources = {}


    # =========================================================
    #                      COMBAT RESET
    # =========================================================

    def reset_combat_state(self):
        self.reset_health()
        self.reset_action_gauge()
        self.reset_buffs()
        self.reset_debuffs()
        self.reset_combat_resources()
        self.extra_turn_pending = False
        self.forced_turn_pending = False
        self._preserve_action_gauge_forced_turn = False
        self.banished = False
        self.special_states = {}
        self.internal_cooldowns = {}
        self.death_order = None
        self._death_recorded = False
        self._battle_state = None
        self._combat_team = []
        self._combat_opponents = []

        for skill in self.skills:
            skill.reset_cooldown()


    # =========================================================
    #                      PROGRESSION
    # =========================================================

    def can_resonate_with(self, other):
        return (
            self.monster_id == other.monster_id 
            and self.resonance < 5 
            and self is not other
        )



    def increase_resonance(self):
        if self.resonance < 5:
            self.resonance += 1


    # =========================================================
    #                      PRESENTATION
    # =========================================================

    def show(self):
        print(f"{self.display_name}   Lvl {self.level}   {'★' * self.rarity}\n\n"
              f"HP: {self.health} / {self.max_health}\n"
              f"Attack: {self.attack}\n"
              f"Defense: {self.defense}\n"
              f"Speed: {self.speed}\n"
              f"CRT Rate: {self.crit_rate}%\n"
              f"CRT Damage: {self.crit_damage}%\n\n"

              "Skills:")
        for i, skill in enumerate(self.skills, start=1):
            print(f"    {i}. {skill.name}")

        print("\nPassives:")
        if self.passives:
            for passive in self.passives:
                print(f"    - {passive.name}")
        else:
            print("    - None")

        print(f"Glyphs:")
        for i, glyph in enumerate(self.glyphs, start=1):
            print(f"    {i}. {glyph}")
        print("\n")


    # =========================================================
    #                  PYTHON SPECIAL METHODS
    # =========================================================

    def __str__(self):
        return f"{self.name} - Health: {self.health}/{self.max_health} - Attack: {self.attack} - Defense: {self.defense}"




