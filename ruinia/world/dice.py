import re
from random import randint
from evennia import default_cmds, CmdSet


def roll_dice(dicenum, dicetype, modifier=None, conditional=None, return_tuple=False):
    """
    This is a standard dice roller.

    Args:
     dicenum (int): Number of dice to roll (the result to be added).
     dicetype (int): Number of sides of the dice to be rolled.
     modifier (tuple): A tuple `(operator, value)`, where operator is
        one of `"+"`, `"-"`, `"/"` or `"*"`. The result of the dice
        roll(s) will be modified by this value.
     conditional (tuple): A tuple `(conditional, value)`, where
        conditional is one of `"=="`,`"<"`,`">"`,`">="`,`"<=`" or "`!=`".
        This allows the roller to directly return a result depending
        on if the conditional was passed or not.
     return_tuple (bool): Return a tuple with all individual roll
        results or not.

    Returns:
        roll_result (int): The result of the roll + modifiers. This is the
             default return.
        condition_result (bool): A True/False value returned if `conditional`
            is set but not `return_tuple`. This effectively hides the result
            of the roll.
        full_result (tuple): If, return_tuple` is `True`, instead
            return a tuple `(result, outcome, diff, rolls)`. Here,
            `result` is the normal result of the roll + modifiers.
            `outcome` and `diff` are the boolean result of the roll and
            absolute difference to the `conditional` input; they will
            be will be `None` if `conditional` is not set. `rolls` is
            itself a tuple holding all the individual rolls in the case of
            multiple die-rolls.

    Raises:
        TypeError if non-supported modifiers or conditionals are given.

    Notes:
        All input numbers are converted to integers.

    Examples:
        print roll_dice(2, 6) # 2d6
        <<< 7
        print roll_dice(1, 100, ('+', 5) # 1d100 + 5
        <<< 34
        print roll_dice(1, 20, conditional=('<', 10) # let'say we roll 3
        <<< True
        print roll_dice(3, 10, return_tuple=True)
        <<< (11, None, None, (2, 5, 4))
        print roll_dice(2, 20, ('-', 2), conditional=('>=', 10), return_tuple=True)
        <<< (8, False, 2, (4, 6)) # roll was 4 + 6 - 2 = 8

    """
    dicenum = int(dicenum)
    dicetype = int(dicetype)

    # roll all dice, remembering each roll
    rolls = tuple([randint(1, dicetype) for roll in range(dicenum)])
    result = sum(rolls)

    if modifier:
        # make sure to check types well before eval
        mod, modvalue = modifier
        if mod not in ("+", "-", "*", "/"):
            raise TypeError("Non-supported dice modifier: %s" % mod)
        modvalue = int(modvalue)  # for safety
        result = eval("%s %s %s" % (result, mod, modvalue))
    outcome, diff = None, None
    if conditional:
        # make sure to check types well before eval
        cond, condvalue = conditional
        if cond not in (">", "<", ">=", "<=", "!=", "=="):
            raise TypeError(
                "Non-supported dice result conditional: %s" % conditional)
        condvalue = int(condvalue)  # for safety
        outcome = eval("%s %s %s" % (result, cond, condvalue))  # True/False
        diff = abs(result - condvalue)
    if return_tuple:
        return result, outcome, diff, rolls
    else:
        if conditional:
            return outcome
        else:
            return result
