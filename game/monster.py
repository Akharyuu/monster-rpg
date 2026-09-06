from .enums import Attribute, EffectType
from .skills import SkillResult

class Monster:
    def __init__(self, monster_id, name, family, attribute, rarity, health, max_health, attack, defense, speed, skills=None, level=1, ascended=False):

        #Atributos
        self.monster_id = monster_id
        self.name = name
        self.family = family
        self.attribute = attribute
        self.rarity = rarity
        self.level = level
        self.ascended = ascended

        #Estadísticas
        self.max_health = max_health
        self.health = health
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.crit_rate = 15
        self.crit_damage = 50

        #Habilidades y Glifos
        if skills is None:
            self.skills = []
        else:
            self.skills = skills

        self.glyphs = []
        self.resonance = 0

        #Buffs y debuffs
        self.buffs = []
        self.debuffs = []


    #Nombre mostrado.
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


    def use_skill(self, defender, skill):
        if skill not in self.skills:
            print(f"{self.name} no conoce la habilidad {skill.name}.")
            return SkillResult(False, None)

        if not skill.is_available():
            print(f"The skill is currently on cooldown. {skill.current_cooldown} turns left.")
            return SkillResult(False, None)
        
        skill_result = skill.execute(self, defender)
        skill.trigger_cooldown()

        return skill_result


    def get_skill(self, index):
        if index not in range(1, len(self.skills) + 1):
            return None

        return self.skills[index -1]


    def receive_damage(self, damage):
        self.health -= damage

        #If enemy receives damage while Frozen, freeze status is removed.
        new_debuffs = []
        for debuff in self.debuffs:
            if debuff.effect_id != "freeze":
                new_debuffs.append(debuff)

        self.debuffs = new_debuffs


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


    def reduce_remaining_turns(self):

        #Buffs
        for buff in self.buffs:
            buff.reduce_remaining_turns()

        active_buffs = []

        for buff in self.buffs:
            if buff.is_active:
                active_buffs.append(buff)

        self.buffs = active_buffs        

        #Debuffs
        for debuff in self.debuffs:
            debuff.reduce_remaining_turns()

        active_debuffs = []

        for debuff in self.debuffs:
            if debuff.is_active:
                active_debuffs.append(debuff)

        self.debuffs = active_debuffs   


    def apply_status_effect(self, effect):

        #Buffs:
        if effect.effect_type == EffectType.BUFF:
            for buff in self.buffs:
                if buff.effect_id == effect.effect_id:
                    if effect.duration > buff.remaining_turns:
                        buff.remaining_turns = effect.duration
                    return True
                
            if len(self.buffs) < 5:   
                self.buffs.append(effect)
                return True

        #Debuffs:
        elif effect.effect_type == EffectType.DEBUFF:

            #Checks for Immunity:
            if self.has_immunity:
                return False
                
            for debuff in self.debuffs:
                if debuff.effect_id == effect.effect_id:

                    #If effect is stackable, adds stacks.
                    if debuff.effect_id == "burn" or debuff.effect_id == "poison":
                        debuff.stacks += effect.stacks

                        if debuff.stacks > debuff.max_stacks:
                            debuff.stacks = debuff.max_stacks

                    #If effect previously existed, refreshes duration with new duration.
                    if effect.duration > debuff.remaining_turns:
                        debuff.remaining_turns = effect.duration

                    return True

            if len(self.debuffs) < 5:
                self.debuffs.append(effect)
                return True
            
        return False


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

                
    def get_effective_stat(self, stat):
        buff_modifier = 1
        debuff_modifier = 1

        for buff in self.buffs:
            if stat == buff.stat:
                buff_modifier = buff.modifier

        for debuff in self.debuffs:
            if stat == debuff.stat:
                debuff_modifier = debuff.modifier

        base = getattr(self, stat)

        return base * buff_modifier * debuff_modifier


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




