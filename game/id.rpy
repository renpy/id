init python in director:
    from store import Action, config
    import store

    state = renpy.session.get("director", None)
    if state is None:

        state = store.NoRollback()

        # Is the directory currently active.
        state.active = False

        # The last line we saw.
        state.line = [ ]

        # The list of lines we've seen recently.
        state.lines = [ ]

        # The mode we're in.
        state.mode = "lines"

        renpy.session["director"] = state

    class Add(Action):

        def __init__(self, filename, line):
            self.filename = filename
            self.line = line

    class Remove(Action):

        def __init__(self, filename, line):
            self.filename = filename
            self.line = line

    def interact():

        # Update the line log.
        lines = renpy.get_line_log()

        if state.line in lines:
            lines.remove(state.line)

        renpy.clear_line_log()

        # Update state.line to the current line.
        state.line = renpy.get_filename_line()

        # State.lines is the list of lines we've just seen, along with
        # the actions used to edit those lines.
        state.lines = [ ]

        for filename, line in lines[:15]:

            if filename.startswith("renpy/"):
                continue

            text = renpy.scriptedit.get_line_text(filename, line)
            stripped = text.lstrip(" ")
            indent = len(text) - len(stripped)
            text = " " * (indent // 4) + stripped

            short_fn = filename.rpartition('/')[2]
            pos = "{}:{:04d}".format(short_fn, line)

            state.lines.append((
                pos,
                text,
                Add(filename, line),
                Remove(filename, line)
            ))

        # Show the director screen.
        if renpy.context_nesting_level() == 0:
            if not renpy.get_screen("director"):
                renpy.show_screen("director")


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



style director_frame is default:
    background "#0000006f"
    xfill True
    ypadding 4

style director_text:
    size 14

style director_button is default

style director_button_text is default:
    size 14


screen director_lines(state):

    vbox:

        for line_pos, line_text, add_action, remove_action in state.lines:
            hbox:
                textbutton "+" action add_action:
                    text_color "#0f0"
                    text_hover_color "#8f8"
                    xpadding 5

                text "[line_pos]"

                textbutton "-" action remove_action:
                    text_color "#f44"
                    text_hover_color "#fcc"
                    text_insensitive_color "#f444"
                    xpadding 5

                text "[line_text]"


screen director():

    style_group "director"

    $ state = director.state

    frame:

        if state.mode == "lines":
            use director_lines(state)



