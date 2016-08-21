# This file contains the script for the Ren'Py demo game. Execution starts at
# the start label.

label main_menu:
    return False

# Declare the characters.
define e = Character(_('Eileen'))

label start:

    scene bg roof

    e "This is nice, but you know what would make this game nicer?"

    show eileen happy

    e "If I showed up right about now."

    e "That's way better, isn't it?"

    return
