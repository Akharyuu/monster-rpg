# =========================================================
#                    PASSIVE TRIGGERS
# =========================================================

def trigger_passives(trigger_name, owner, context):

    context["trigger"] = trigger_name

    for passive in owner.passives:

        if passive.trigger is None:
            continue

        triggers = passive.trigger

        if isinstance(triggers, str):
            triggers = [triggers]

        if trigger_name in triggers:
            passive.activate(owner, context)