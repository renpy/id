# This file contains the script for the Ren'Py demo game. Execution starts at
# the start label.

label main_menu:
    return False

# Declare the characters.
define e = Character(_('Eileen'), color="#c8ffc8")

screen test:
    zorder 100
    textbutton "Start Director" action director.Start() xalign 1.0 yalign 1.0

label start:

    show screen test

    "A"
    "B"
    "C"
    "D"
    "E"
    "F"
    "G"
    "H"

    return
