import random
from .enums import Attribute

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


    def use_skill(self, defender, skill):
        if skill not in self.skills:
            print(f"{self.name} no conoce la habilidad {skill.name}.")
            return 0, False

        if not skill.is_available():
            print(f"The skill is currently on cooldown. {skill.current_cooldown} turns left.")
            return None, False
        
        damage, critical = skill.damage_calc(self, defender)
        defender.receive_damage(damage)
        skill.trigger_cooldown()

        return damage, critical


    def receive_damage(self, damage):
        self.health -= damage


    def heal(self, value):
        base_health = self.health
        self.health += value
        return self.health - base_health


    def learn_skill(self, skill):
        if skill not in self.skills and len(self.skills) < 4:
            self.skills.append(skill)
            return "aprendida"

        if skill in self.skills:
            return "repetida"

        return "limite"


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
            print(f"    {i}. {skill.name} - Power: {skill.power}")

        print(f"Glyphs:")
        for i, glyph in enumerate(self.glyphs, start=1):
            print(f"    {i}. {glyph}")
        print("\n")


    def get_skill(self, index):
        if index not in range(1, len(self.skills) + 1):
            return None

        return self.skills[index -1]


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



#====================================================================================================================================

class Skill:
    def __init__(self, name, power, cooldown=0):
        self.name = name
        self.power = power
        self.cooldown = cooldown
        self.current_cooldown = 0


    def damage_calc(self, attacker, defender):
        critical = False
        damage = attacker.attack + self.power - defender.defense

        if damage <= 0:
            return 0, critical

        #Attribute Advantage
        modifier = attacker.get_attribute_modifier(defender)
        damage *= modifier

        #Crit Roll
        if random.randint(1, 100) <= attacker.crit_rate:
            damage *= 1 + attacker.crit_damage / 100
            critical = True
        
        return int(damage), critical


    def is_available(self):
        return self.current_cooldown == 0


    def trigger_cooldown(self):
        self.current_cooldown = self.cooldown


    def reduce_cooldown(self):
        self.current_cooldown -= 1

        if self.current_cooldown < 0:
            self.current_cooldown = 0


    def __eq__(self, other):
        if isinstance(other, Skill):
            return self.name == other.name and self.power == other.power
        return False


    def __repr__(self):
        return f"Skill({self.name, self.power})"
    


    