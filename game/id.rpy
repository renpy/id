init python in director:
    from store import Action, config
    import store

    state = renpy.session.get("director", None)
    if state is None:

        state = store.NoRollback()

        # Is the directory currently active.
        state.active = False

        # The list of lines we've seen recently.
        state.lines = [ ]

        # The last line we saw.
        state.line = [ ]


        renpy.session["director"] = state


    def interact():

        # Update the line log.
        lines = renpy.get_line_log()

        if state.line in lines:
            lines.remove(state.line)

        state.lines = lines

        renpy.clear_line_log()

        # Update state.line.
        state.line = renpy.get_filename_line()

        # Show the director screen.
        if renpy.context_nesting_level() == 0:
            if not renpy.get_screen("_director"):
                renpy.show_screen("_director")


    if state.active:
        config.clear_lines = False
        config.line_log = True

        config.start_interact_callbacks.append(interact)

    class Start(Action):
        """
        The action that starts the director.
        """

        def __call__(self):
            if state.active:
                return

            renpy.session["compile"] = True
            state.active = True

            store._reload_game()

        def get_sensitive(self):
            return not state.active




screen _director:
    vbox:
        hbox:
            textbutton "Add" action renpy.scriptedit.test_add
            $ filename, linenumber = renpy.get_filename_line()
            text "[filename]:[linenumber]"
            textbutton "Remove" action renpy.scriptedit.test_remove

        for filename, linenumber in director.state.lines:
            $ lt = renpy.scriptedit.get_line_text(filename, linenumber)
            text "[filename]:[linenumber] [lt]" size 12
