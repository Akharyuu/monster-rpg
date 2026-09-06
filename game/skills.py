import random
from .enums import SkillType, EffectType
from .status_effect_data import STATUS_EFFECT_DATA
from .status_effect import StatusEffect

class Skill:
    def __init__(self, skill_id, name, cooldown=0):
        self.skill_id = skill_id
        self.name = name
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
    def __init__(self, skill_id, name, power, effects=None, cooldown=0):
        super().__init__(skill_id, name, cooldown)
        self.skill_type = SkillType.DAMAGE
        self.power = power
        if effects is not None:
            self.effects = effects
        else: 
            self.effects = []


    def damage_calc(self, attacker, defender):
            critical = False

            #Apply buffs and debuffs
            effective_attack = attacker.get_effective_stat("attack")
            effective_defense = defender.get_effective_stat("defense")

            damage = effective_attack + self.power - effective_defense
    
            if damage <= 0:
                return 1, critical
    
            #Attribute Advantage
            modifier = attacker.get_attribute_modifier(defender)
            damage *= modifier
    
            #Crit Roll
            if random.randint(1, 100) <= attacker.crit_rate:
                damage *= 1 + attacker.crit_damage / 100
                critical = True
            
            return int(damage), critical


    def execute(self, caster, target):
        damage, critical = self.damage_calc(caster, target)
        target.receive_damage(damage)

        for effect in self.effects:
            chance = random.random()

            if chance <= effect["chance"]:
                effect_data = STATUS_EFFECT_DATA[effect["effect_id"]]

                status_effect = StatusEffect(
                    effect_id=effect["effect_id"],
                    name=effect_data["name"],
                    stat=effect_data["stat"],
                    effect_type=effect_data["effect_type"],
                    modifier=effect_data["modifier"],
                    duration=effect["turns"],
                    stacks=effect.get("stacks", 1),
                    max_stacks=effect_data.get("max_stacks", 1)
                )

                if effect_data["effect_type"] == EffectType.BUFF:
                    caster.apply_status_effect(status_effect)

                elif effect_data["effect_type"] == EffectType.DEBUFF:
                    target.apply_status_effect(status_effect)

        skill_result = SkillResult(True, damage, critical)

        return skill_result



class HealingSkill(Skill):
    def __init__(self, skill_id, name, scaling_stat, base_scaling_ratio, scaling_bonus=0, cooldown=0):
        super().__init__(skill_id, name, cooldown)
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


    def execute(self, caster, target):
        heal_value = self.healing(caster, target)

        skill_result = SkillResult(True, heal_value)

        return skill_result



class SkillResult():
    def __init__(self, success, value, critical=False, effect_applied=None):
        self.success = success
        self.value = value
        self.critical = critical
        self.effect_applied = effect_applied

