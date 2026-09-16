class StatusEffect():
    def __init__(self, effect_id, name, stat, effect_type, modifier, duration, stacks=1, max_stacks=1, source=None, modifier_mode="multiplicative"):
        self.effect_id = effect_id
        self.name = name
        self.stat = stat
        self.effect_type = effect_type
        self.modifier = modifier
        self.duration = duration
        self.remaining_turns = duration
        self.stacks = stacks
        self.max_stacks = max_stacks
        self.source = source
        self.modifier_mode = modifier_mode


    @property
    def is_active(self):
        return self.remaining_turns > 0


    def reduce_remaining_turns(self):
        self.remaining_turns -= 1
        if self.remaining_turns < 0:
            self.remaining_turns = 0