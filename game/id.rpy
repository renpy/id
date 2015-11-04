init python in director:
    from store import Action, config
    import store

    # A set of tags that will not be show to the user.
    tag_blacklist = {
        "black",
        "text",
        "vtext",
    }

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

        # The filename and linenumber of the line we're editing,
        state.filename = ""
        state.linenumber = 0

        # The tag we're updating.
        state.tag = ""

        # The attributes of the image we're updating.
        state.attributes = [ ]

        # Has the new line been added to ast.
        state.added_statement = None

        renpy.session["director"] = state

    class Add(Action):

        def __init__(self, filename, linenumber):
            self.filename = filename
            self.linenumber = linenumber

        def __call__(self):

            state.filename = self.filename
            state.linenumber = self.linenumber

            state.mode = "show"
            state.tag = None
            state.attributes = [ ]
            state.added_statement = None

            update_add()

    class SetTag(Action):

        def __init__(self, tag):
            self.tag = tag

        def __call__(self):
            state.tag = self.tag
            state.attributes = [ ]

            update_add()

        def get_selected(self):
            return self.tag == state.tag

    class ToggleAttribute(Action):

        def __init__(self, attribute):
            self.attribute = attribute

        def __call__(self):
            if self.attribute in state.attributes:
                state.attributes.remove(self.attribute)
            else:
                state.attributes.append(self.attribute)

            update_add()

        def get_selected(self):
            return self.attribute in state.attributes

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


    def init():
        config.clear_lines = False
        config.line_log = True

        config.start_interact_callbacks.append(interact)

    if state.active:
        init()

    def command():
        if not state.active:
            state.active = True
            init()

        return True

    renpy.arguments.register_command("director", command)

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

    def get_tags():
        rv = [ i for i in renpy.get_available_image_tags() if not i.startswith("_") if i not in tag_blacklist ]
        rv.sort(key=lambda a : a.lower())
        return rv

    def get_attributes():
        if not state.tag:
            return [ ]

        rv = set()

        for i in renpy.get_available_image_attributes(state.tag, state.attributes):
            for j in i:
                rv.add(j)

        rv = list(rv)
        rv.sort(key = lambda a : a.lower())
        return rv

    def get_statement():
        l = renpy.get_available_image_attributes(state.tag, state.attributes)

        if len(l) != 1:
            return None

        rv = [ "show" ]

        rv.append(state.tag)
        rv.extend(l[0])

        return " ".join(rv)

    def update_add():

        statement = get_statement()

        if state.added_statement == statement:
            renpy.restart_interaction()
            return

        if state.added_statement is not None:
            renpy.scriptedit.remove_from_ast(state.filename, state.linenumber)

        if statement:
            renpy.scriptedit.add_to_ast_before(statement, state.filename, state.linenumber)

        state.added_statement = statement
        renpy.rollback(checkpoints=0, force=True, greedy=True)


style director_frame is default:
    background "#0000006f"
    xfill True
    ypadding 4
    xpadding 5

style director_text:
    size 16

style director_label

style director_label_text:
    size 16

style director_button is default:
    xpadding 5

style director_button_text is default:
    size 16
    color "#c0c0c0"
    hover_color "#ffffff"
    selected_color "#ffffc0"


screen director_lines(state):

    vbox:

        for line_pos, line_text, add_action, remove_action in state.lines:
            hbox:
                textbutton "+" action add_action:
                    text_color "#0f0"
                    text_hover_color "#8f8"

                text "[line_pos]"

                textbutton "-" action remove_action:
                    text_color "#f44"
                    text_hover_color "#fcc"
                    text_insensitive_color "#f444"

                text "[line_text]"

screen director_show(state):

    $ statement = director.get_statement()

    vbox:
        hbox:
            box_wrap True

            label "tag:"

            for t in director.get_tags():
                textbutton "[t]" action director.SetTag(t)


        null height 4

        hbox:
            box_wrap True

            label "attributes:"

            for a in director.get_attributes():
                textbutton "[a]" action director.ToggleAttribute(a)

        null height 4

        if statement:
            text "[statement!q]"


screen director():

    style_group "director"

    $ state = director.state

    frame:

        if state.mode == "lines":
            use director_lines(state)
        elif state.mode == "show" or state.mode == "scene":
            use director_show(state)





