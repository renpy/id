# This file contains the script for the Ren'Py demo game. Execution starts at
# the start label.


image lucy beach happy = Placeholder()
image lucy beach mad = Placeholder()
image lucy uniform happy = Placeholder()
image lucy uniform mad = Placeholder()

label main_menu:
    return False

# Declare the characters.
define e = Character(_('Eileen'))

label start:

    pause

    scene bg roof

    e "This is nice, but you know what would make this game way way way way way way nicer?"

    jump rest

    "Ignore this line."

label rest:

    e "If I showed up right about now."

    e "That's way better, isn't it?"

    return
