from .enums import Attribute, EffectType
from .skills import SkillResult
from ..combat.passive_triggers import trigger_passives
from ..data.passive_data import PASSIVE_DATA
from ..data.glyph_stat_data import GLYPH_STAT_MAP
from ..data.glyph_set_data import GLYPH_SET_DATA

class Monster:
    def __init__(self, monster_id, name, family, attribute, rarity, health, max_health, attack, defense, speed, 
                 skills=None, passives=None, level=1, ascended=False, combat_resources=None):

        #Attributes
        self.monster_id = monster_id
        self.name = name
        self.family = family
        self.attribute = attribute
        self.rarity = rarity
        self.level = level
        self.ascended = ascended
        self.action_gauge = 0
        self.resonance = 0

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

    @property
    def display_name(self):
        if self.ascended:
            return self.name

        return f"{self.attribute.value} {self.family}"

    @property
    def is_alive(self):
        return self.health > 0

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
    def cannot_act(self):
        return self.is_stunned or self.is_frozen

    @property
    def is_silenced(self):
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


    def has_passive_trait(self, trait):
        for passive in self.passives:
            data = PASSIVE_DATA[passive.skill_id]

            if trait in data.get("traits", []):
                return True

        return False


#Glyph methods
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


#Action Gauge methods
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


#Skill methods
    def use_skill(self, targets, skill):

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

        # Passives that activate before the skill.
        trigger_passives(
            "before_skill",
            self,
            context
        )

        skill_result = skill.execute(
            self,
            targets
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


    def get_skill(self, index):
        if index not in range(1, len(self.skills) + 1):
            return None

        return self.skills[index -1]


    def receive_damage(self, damage, source=None):
        self.health -= damage

        broken_effects = []

        preserve_freeze = (
            source is not None
            and source.has_passive_trait("preserve_freeze_on_hit")
        )

        new_debuffs = []

        for debuff in self.debuffs:

            if debuff.effect_id == "freeze" and not preserve_freeze:
                broken_effects.append(debuff)
                continue

            new_debuffs.append(debuff)

        self.debuffs = new_debuffs

        return broken_effects


    def get_attribute_modifier(self, defender):
        if ((self.attribute == Attribute.IGNEOUS and defender.attribute == Attribute.ABYSSAL) or 
            (self.attribute == Attribute.ABYSSAL and defender.attribute == Attribute.STORM) or
            (self.attribute == Attribute.STORM and defender.attribute == Attribute.IGNEOUS)):
            return 0.8

        elif ((self.attribute == Attribute.IGNEOUS and defender.attribute == Attribute.STORM) or 
            (self.attribute == Attribute.ABYSSAL and defender.attribute == Attribute.IGNEOUS) or
            (self.attribute == Attribute.STORM and defender.attribute == Attribute.ABYSSAL)):
            return 1.2

        else:
            return 1


    def heal(self, value):
        base_health = self.health
        self.health += value
        return self.health - base_health


    def reduce_skill_cooldowns(self):
        for skill in self.skills:
            skill.reduce_cooldown()


#Buff/Debuff methods
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


    def apply_status_effect(self, effect):

        if effect.effect_type == EffectType.BUFF:
            effects_list = self.buffs

        elif effect.effect_type == EffectType.DEBUFF:
            if self.has_immunity:
                return None

            effects_list = self.debuffs

        else:
            return None

        for active_effect in effects_list:
            if active_effect.effect_id == effect.effect_id:

                if active_effect.effect_id in ("burn", "poison"):
                    active_effect.stacks += effect.stacks

                    if active_effect.stacks > active_effect.max_stacks:
                        active_effect.stacks = active_effect.max_stacks

                if effect.duration > active_effect.remaining_turns:
                    active_effect.remaining_turns = effect.duration

                # Update who applied/refreshed the effect.
                active_effect.source = effect.source

                return active_effect

        if len(effects_list) < 5:
            effects_list.append(effect)
            return effect

        return None


    def apply_damage_over_time(self):
        total_damage = 0

        for debuff in self.debuffs:
            if debuff.effect_id == "burn":

                if debuff.stacks == 1:
                    damage = self.max_health * 0.03 
                elif debuff.stacks == 2:
                    damage = self.max_health * 0.06 
                elif debuff.stacks == 3:
                    damage = self.max_health * 0.1 

                total_damage += damage

            elif debuff.effect_id == "poison":
                damage = self.max_health * 0.05 * debuff.stacks
                total_damage += damage

        if total_damage > 0:
            self.health -= int(total_damage)
            print(f"{self.display_name} takes {int(total_damage)} damage from DoT.")
            print()


    def get_equipped_stat(self, stat):

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

        return (
            base * multiplicative_modifier
            + additive_modifier
        )


#Combat resources methods (passive stuff/charges...)
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


#Other methods
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


    def can_resonate_with(self, other):
        return (
            self.monster_id == other.monster_id 
            and self.resonance < 5 
            and self is not other
        )


    def increase_resonance(self):
        if self.resonance < 5:
            self.resonance += 1

        
    def __str__(self):
        return f"{self.name} - Health: {self.health}/{self.max_health} - Attack: {self.attack} - Defense: {self.defense}"




