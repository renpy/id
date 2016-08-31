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

        # Should the director screen be shown.
        state.show_director = False

        # The list of lines we've seen recently.
        state.lines = [ ]

        # The mode we're in.
        state.mode = "lines"

        # The filename and linenumber of the line we're editing,
        state.filename = ""
        state.linenumber = 0


        # What kind of statement is this?
        state.kind = "show"

        # The tag we're updating.
        state.tag = ""
        state.original_tag = ""

        # The attributes of the image we're updating.
        state.attributes = [ ]
        state.original_attributes = [ ]

        # Has the new line been added to ast.
        state.added_statement = None

        # Are we changing the script? (Does the node needed to be removed?)
        state.change = False

        renpy.session["director"] = state

    class Add(Action):

        def __init__(self, filename, linenumber):
            self.filename = filename
            self.linenumber = linenumber

        def __call__(self):

            state.filename = self.filename
            state.linenumber = self.linenumber

            state.kind = "show"
            state.mode = "tag"
            state.tag = None
            state.attributes = [ ]
            state.original_tag = None
            state.original_attributes = [ ]
            state.added_statement = None

            state.change = False

            update_add()

    class Change(Action):

        def __init__(self, filename, linenumber, node):
            self.filename = filename
            self.linenumber = linenumber


            if isinstance(node, renpy.ast.Show):
                self.kind = "show"

            self.tag = node.imspec[0][0]
            self.attributes = list(node.imspec[0][1:])

        def __call__(self):
            state.filename = self.filename
            state.linenumber = self.linenumber

            state.kind = self.kind
            state.mode = "attributes"
            state.tag = self.tag
            state.attributes = self.attributes
            state.original_tag = self.tag
            state.original_attributes = list(self.attributes)
            state.added_statement = True

            state.change = True

            update_add()


    class SetTag(Action):

        def __init__(self, tag):
            self.tag = tag

        def __call__(self):

            if state.tag != self.tag:

                state.tag = self.tag
                state.attributes = [ ]

                state.mode = "attributes"


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

                compatible = set()

                for i in renpy.get_available_image_attributes(state.tag, [ self.attribute ]):
                    for j in i:
                        compatible.add(j)

                state.attributes = [ i for i in state.attributes if i in compatible ]


            update_add()

        def get_selected(self):
            return self.attribute in state.attributes

    def interact():
        # Update the line log.
        lines = renpy.get_line_log()

        renpy.clear_line_log()

        # Update state.line to the current line.
        state.line = renpy.get_filename_line()

        # State.lines is the list of lines we've just seen, along with
        # the actions used to edit those lines.
        state.lines = [ ]

        for filename, line, node in lines[:30]:

            if not isinstance(node, (renpy.ast.Show, renpy.ast.Scene, renpy.ast.Say)):
                continue

            if filename.startswith("renpy/"):
                continue

            text = renpy.scriptedit.get_line_text(filename, line)
#             stripped = text.lstrip(" ")
#             indent = len(text) - len(stripped)
#             text = " " * (indent // 4) + stripped
            text = text.strip()

            short_fn = filename.rpartition('/')[2]
            pos = "{}:{:04d}".format(short_fn, line)

            add_action = Add(filename, line),

            if isinstance(node, renpy.ast.Show):
                change_action = Change(filename, line, node)
            else:
                change_action = None

            state.lines.append((
                pos,
                text,
                add_action,
                change_action,
            ))

        # Show the director screen.
        if state.show_director and (renpy.context_nesting_level() == 0):
            if not renpy.get_screen("director"):
                renpy.show_screen("director")
        else:
            if renpy.get_screen("director"):
                renpy.hide_screen("director")


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

            state.show_director = True
            state.mode = "lines"

            if state.active:

                renpy.show_screen("director")

                renpy.restart_interaction()
                return

            renpy.session["compile"] = True
            renpy.session["_greedy_rollback"] = True

            state.active = True

            store._reload_game()

        def get_sensitive(self):
            return (not state.active) or (not state.show_director)

    class Stop(Action):

        def __call__(self):
            state.show_director = False

            if renpy.get_screen("director"):
                renpy.hide_screen("director")

            renpy.restart_interaction()

    def get_tags():
        rv = [ i for i in renpy.get_available_image_tags() if not i.startswith("_") if i not in tag_blacklist ]
        rv.sort(key=lambda a : a.lower())
        return rv

    def get_attributes():
        if not state.tag:
            return [ ]

        import collections

        attrcount = collections.defaultdict(int)
        attrtotalpos = collections.defaultdict(float)


        for attrlist in renpy.get_available_image_attributes(state.tag, [ ]):
            for i, attr in enumerate(attrlist):
                attrcount[attr] += 1
                attrtotalpos[attr] += i

        l = [ ]

        for attr in attrcount:
            l.append((attrtotalpos[attr] / attrcount[attr], attr))

        l.sort()
        return [ i[1] for i in l ]

    def get_image_attributes():

        if state.tag is None:
            return None

        l = renpy.get_available_image_attributes(state.tag, state.attributes)

        if len(l) != 1:
            return None

        if len(l[0]) != len(state.attributes):
            return None

        return l[0]

    def get_statement():

        if state.tag is None:
            return None

        l = renpy.get_available_image_attributes(state.tag, state.attributes)

        attributes = get_image_attributes()

        if attributes is None:
            return

        rv = [ "show" ]

        rv.append(state.tag)
        rv.extend(attributes)

        return " ".join(rv)

    def get_ordered_attributes():

        attrs = get_image_attributes()

        if attrs is not None:
            return attrs

        return state.attributes


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

    class Commit(Action):

        def __call__(self):
            statement = get_statement()

            if state.change:
                renpy.scriptedit.remove_line(state.filename, state.linenumber)

            if statement:
                renpy.scriptedit.insert_line_before(statement, state.filename, state.linenumber)

            state.mode = "lines"
            renpy.clear_line_log()
            renpy.rollback(checkpoints=0, force=True, greedy=True)

    class Reset(Action):

        def __call__(self):

            state.tag = state.original_tag
            state.attributes = state.original_attributes

            update_add()

    class Cancel(Action):

        def __call__(self):

            state.tag = state.original_tag
            state.attributes = state.original_attributes

            state.mode = "lines"

            renpy.clear_line_log()
            update_add()

    class Remove(Action):

        def __call__(self):

            if state.change:
                renpy.scriptedit.remove_line(state.filename, state.linenumber)

            state.tag = None
            state.mode = "lines"

            renpy.clear_line_log()
            update_add()

style director_frame is _frame:
    xfill True
    yfill False
    yalign 0.0
    background "#d0d0d0d0"
    ypadding 0


style director_text is _text:
    size 20

style director_label

style director_label_text is director_text:
    bold True

style director_button is empty

style director_button_text is director_text:
    color "#405060"
    hover_color "#048"
    insensitive_color "#00000020"
    selected_color "#0099cc"


style director_edit_button is director_button:
    xsize 40
    xpadding 10

style director_edit_button_text is director_button_text:
    font "DejaVuSans.ttf"
    xalign 0.5

style director_action_button is director_button

style director_action_button_text is director_button_text:
    size 24

style director_statement_button is director_button

style director_statement_button_text is director_button_text:
    size 22


screen director_lines(state):

    frame:
        style "empty"
        background Solid("#fff8", xsize=20, xpos=189)

        has vbox

        for line_pos, line_text, add_action, change_action in state.lines:

            hbox:
                text " ":
                    min_width 179
                    style "director_text"

                textbutton "+" action add_action style "director_edit_button"

            hbox:

                text "[line_pos]":
                    min_width 179
                    text_align 1.0
                    style "director_text"

                if change_action:
                    textbutton "✎" action change_action style "director_edit_button"
                else:
                    textbutton " " action change_action style "director_edit_button"

                text "[line_text]":
                    style "director_text"

        hbox:
            text " ":
                min_width 179
                style "director_text"

            textbutton " ":
                action None
                style "director_edit_button"
                ysize 40

            hbox:
                yalign 1.0

                textbutton "Done":
                    action director.Stop()
                    style "director_action_button"



screen director_statement(state):

    $ tag = state.tag or "(tag)"
    $ attributes =  " ".join(director.get_ordered_attributes()) or "(attributes)"

    hbox:
        style_prefix "director_statement"

        textbutton "[state.kind] "
        textbutton "[tag] " action SetField(state, "mode", "tag")
        textbutton "[attributes] " action SetField(state, "mode", "attributes")

    null height 14

screen director_footer(state):

    null height 14


    hbox:
        style_prefix "director_action"

        spacing 26

        if state.change:
            textbutton "Change" action If(director.get_statement(), director.Commit())
        else:
            textbutton "Add" action If(director.get_statement(), director.Commit())


        textbutton "Cancel" action director.Cancel()

        if state.change:
            textbutton "Remove" action director.Remove()


screen director_tag(state):

    vbox:

        use director_statement(state)

        text "Tag:" size 20

        frame:
            style "empty"
            left_margin 10

            hbox:

                box_wrap True
                spacing 20

                for t in director.get_tags():
                    textbutton "[t]":
                        action director.SetTag(t)

        use director_footer(state)

screen director_attributes(state):

    vbox:

        use director_statement(state)

        text "Attributes:"

        frame:
            style "empty"
            left_margin 10

            hbox:
                box_wrap True
                spacing 20

                for t in director.get_attributes():
                    textbutton "[t]":
                        action director.ToggleAttribute(t)
                        style "director_button"
                        ypadding 0

        use director_footer(state)


screen director():

    $ state = director.state

    frame:
        style_prefix "director"

        if state.mode == "lines":
            use director_lines(state)
        elif state.mode == "tag":
            use director_tag(state)
        elif state.mode == "attributes":
            use director_attributes(state)


