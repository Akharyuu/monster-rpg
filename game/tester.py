from game.combat.balance_analyzer import (
    analyze_five_drake_contextual_balance
)


# =========================================================
#          FIVE DRAKE CONTEXTUAL BALANCE
# =========================================================

analyze_five_drake_contextual_balance(
    runs=500,
    resonance=5,
    level=50,
    ascended=True,
    attribute_targeting=False
)