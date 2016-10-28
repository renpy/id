# Copyright 2016 Tom Rothamel <pytom@bishoujo.us>

# Permission to use, copy, modify, and/or distribute this software for
# non-commerical purposes is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# For the purpose of this license, when using this software to develop a
# another software program, this program is being used commerically if
# payment is required to distribute that program, to use that program, or
# to access any feature in that program, or if the program presents
# advertising to its user.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
# OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

init -100 python in director:
    from store import Action, config
    import store

    # A set of tags that will not be show to the user.
    tag_blacklist = {
        "black",
        "text",
        "vtext",
    }

    # A set of tags that should only be used with the scene statement.
    scene_tags = { "bg" }

    # A list of transforms to use.
    transforms = [ "left", "center", "right" ]

    # Is the director licensed for commercial use? Yes, you can remove
    # the warning by changing this variable - but it doesn't change the
    # license of the director tool.
    commercial = False

    # Should we offer a button to access the director?
    button = True

    state = renpy.session.get("director", None)

    # Initialize the state object if it doesn't exist.
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
        state.kind = None
        state.original_kind = None

        # The tag we're updating.
        state.tag = ""
        state.original_tag = ""

        # The attributes of the image we're updating.
        state.attributes = [ ]
        state.original_attributes = [ ]

        # The transforms applied to the image.
        state.transforms = [ ]
        state.original_transforms = [ ]

        # Has the new line been added to ast.
        state.added_statement = None

        # Are we changing the script? (Does the node needed to be removed?)
        state.change = False

        renpy.session["director"] = state

    def interact():
        """
        This is called once per interaction, to update the list of lines
        being displayed, and also to show or hide the director as appropriate.
        """

        show_director = False

        # Update the line log.
        lines = renpy.get_line_log()
        renpy.clear_line_log()

        # Update state.line to the current line.
        state.line = renpy.get_filename_line()

        # State.lines is the list of lines we've just seen, along with
        # the actions used to edit those lines.
        for _filename, _line, node in lines[-30:]:
            if isinstance(node, renpy.ast.Say):
                state.lines = [ ]
                break

        for filename, line, node in lines[-30:]:

            if filename.startswith("renpy/"):
                show_director = False
                continue
            else:
                show_director = True

            if not isinstance(node, (renpy.ast.Show, renpy.ast.Scene, renpy.ast.Say)):
                continue

            text = renpy.scriptedit.get_line_text(filename, line)
            text = text.strip()

            short_fn = filename.rpartition('/')[2]
            pos = "{}:{:04d}".format(short_fn, line)

            add_action = AddStatement(filename, line)

            if isinstance(node, (renpy.ast.Show, renpy.ast.Scene)):
                change_action = ChangeStatement(filename, line, node)
            else:
                change_action = None

            state.lines.append((
                pos,
                text,
                add_action,
                change_action,
            ))

        # Show the director screen.
        if show_director and state.show_director and (renpy.context_nesting_level() == 0):
            if not renpy.get_screen("director"):
                renpy.show_screen("director")
        else:
            if renpy.get_screen("director"):
                renpy.hide_screen("director")


    def init():
        """
        This is called once at game start, to reconfigured Ren'Py to
        support the ID.
        """

        config.clear_lines = False
        config.line_log = True

        config.start_interact_callbacks.append(interact)

    if state.active:
        init()

    def command():
        """
        This can be used to invoke the ID from the command line.
        """

        if not state.active:
            state.active = True
            init()

        return True

    renpy.arguments.register_command("director", command)


    def get_statement():
        """
        If a statement is defined enough to implement, returns the text
        that can be added to the AST. Otherwise, returns None.
        """

        if state.kind is None:
            return None

        if state.tag is None:
            return None

        l = renpy.get_available_image_attributes(state.tag, state.attributes)

        attributes = get_image_attributes()

        if attributes is None:
            return

        rv = [ state.kind ]

        rv.append(state.tag)
        rv.extend(attributes)

        rv = " ".join(rv)

        if state.transforms:
            rv += " at " + ", ".join(state.transforms)

        return rv

    def update_ast():
        """
        Updates the abstract syntax tree to match the current state, forcing
        a rollback if something significant has changed. This always forces
        an interaction restart.
        """

        statement = get_statement()

        if state.added_statement == statement:
            renpy.restart_interaction()
            return

        linenumber = state.linenumber

        if statement:
            renpy.scriptedit.add_to_ast_before(statement, state.filename, linenumber)
            linenumber += 1

        if state.added_statement is not None:
            renpy.scriptedit.remove_from_ast(state.filename, linenumber)

        state.added_statement = statement

        renpy.rollback(checkpoints=0, force=True, greedy=True)

    def pick_tag():
        """
        If there is only one valid tag, choose it and move to attribute mode.
        """

        tags = get_tags()

        if state.mode != "tag":
            return

        if len(tags) != 1:
            return

        state.tag = tags[0]
        state.mode = "attributes"


    # Screen support functions #################################################

    def get_tags():
        """
        Returns a list of tags that are valid for the current statement kind.
        """

        if state.kind == "scene":
            rv = [ i for i in renpy.get_available_image_tags() if not i.startswith("_") if i not in tag_blacklist if i in scene_tags ]
        elif state.kind == "show":
            rv = [ i for i in renpy.get_available_image_tags() if not i.startswith("_") if i not in tag_blacklist if i not in scene_tags ]
        else:
            rv = [ ]

        rv.sort(key=lambda a : a.lower())
        return rv

    def get_attributes():
        """
        Returns a list of attributes that are valid for the current tag.
        """

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

    def get_transforms():
        """
        Returns a list of transforms that are valid for the current tag.
        """

        return transforms

    def get_image_attributes():
        """
        Returns the list of attributes in the current image, or None if
        no image is known.
        """

        if state.tag is None:
            return None

        l = renpy.get_available_image_attributes(state.tag, state.attributes)

        if len(l) != 1:
            return None

        if len(l[0]) != len(state.attributes):
            return None

        return l[0]

    def get_ordered_attributes():
        """
        Returns the list of attributes in the order they appear in the
        current image (if known), or in the order they were selected
        otherwise.
        """

        attrs = get_image_attributes()

        if attrs is not None:
            return attrs

        return state.attributes


    # Actions ##################################################################

    class Start(Action):
        """
        This action starts the director and displays the lines screen.
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
        """
        This hides the director interface.
        """

        def __call__(self):
            state.show_director = False

            if renpy.get_screen("director"):
                renpy.hide_screen("director")

            renpy.restart_interaction()


    class AddStatement(Action):
        """
        An action that adds a new statement before `filename`:`linenumber`.
        """

        def __init__(self, filename, linenumber):
            self.filename = filename
            self.linenumber = linenumber

        def __call__(self):

            state.filename = self.filename
            state.linenumber = self.linenumber

            state.kind = None
            state.mode = "kind"
            state.tag = None
            state.original_tag = None
            state.attributes = [ ]
            state.original_attributes = [ ]
            state.transforms = [ ]
            state.original_transforms = [ ]

            state.added_statement = None
            state.change = False

            update_ast()

    class ChangeStatement(Action):
        """
        An action that changes the statement at `filename`:`linenumber`.

        `node`
            Should be the AST node corresponding to that statement.
        """

        def __init__(self, filename, linenumber, node):
            self.filename = filename
            self.linenumber = linenumber

            if isinstance(node, renpy.ast.Show):
                self.kind = "show"
            elif isinstance(node, renpy.ast.Scene):
                self.kind = "scene"

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

            print("Need to add support for changing transforms!")
            state.transforms = [ ]
            state.original_transforms = [ ]

            state.added_statement = True
            state.change = True

            update_ast()

    class SetKind(Action):

        def __init__(self, kind):
            self.kind = kind

        def __call__(self):

            if self.kind != state.kind:
                state.kind = self.kind
                state.tag = None
                state.attributes = [ ]

            if self.kind in ("scene", "show"):
                state.mode = "tag"
                pick_tag()

            update_ast()

    class SetTag(Action):
        """
        An action that sets the image tag.
        """

        def __init__(self, tag):
            self.tag = tag

        def __call__(self):

            if state.tag != self.tag:

                state.tag = self.tag
                state.attributes = [ ]

            state.mode = "attributes"

            update_ast()

        def get_selected(self):
            return self.tag == state.tag

    class ToggleAttribute(Action):
        """
        This action toggles on and off an attribute. If an attribute being
        toggled on conflicts with other attributes, those attributes are
        removed.

        Then the AST is updated.
        """

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


            update_ast()

        def get_selected(self):
            return self.attribute in state.attributes

    class ToggleTransform(Action):
        """
        This action toggles to a transform, and if clicked again removes the
        transform.
        """

        def __init__(self, transform):
            self.transform = transform

        def __call__(self):
            if self.transform in state.transforms:
                state.transforms.remove(self.transform)
            else:
                state.transforms = [ self.transform ]

            update_ast()

        def get_selected(self):
            return self.transform in state.transforms

    class AddTransform(Action):
        """
        This action adds a transform to the end of the list of transforms.
        If clicked again, it removes the transform.
        """

        def __init__(self, transform):
            self.transform = transform

        def __call__(self):
            if self.transform in state.transforms:
                state.transforms.remove(self.transform)
            else:
                state.transforms.append(self.transform)

            update_ast()

        def get_selected(self):
            return self.transform in state.transforms


    class Commit(Action):
        """
        Commits the current statement to the .rpy files.
        """

        def __call__(self):
            statement = get_statement()

            if state.change:
                renpy.scriptedit.remove_line(state.filename, state.linenumber)

            if statement:
                renpy.scriptedit.insert_line_before(statement, state.filename, state.linenumber)

            state.mode = "lines"
            renpy.clear_line_log()
            renpy.rollback(checkpoints=0, force=True, greedy=True)

        def get_sensitive(self):
            return get_statement()

    class Reset(Action):
        """
        This action resets the AST to what it was when we started adjusting the
        statement.
        """

        def __call__(self):

            state.kind = state.original_kind
            state.tag = state.original_tag
            state.attributes = state.original_attributes
            state.transforms = state.original_transforms

            if state.kind is None:
                state.mode = "kind"
            elif state.tag is None:
                state.mode = "tag"

            update_ast()

    class Cancel(Action):
        """
        This action cancels the operation, resetting the AST and returning to
        the lines screen.
        """

        def __call__(self):

            state.kind = state.original_kind
            state.tag = state.original_tag
            state.attributes = state.original_attributes
            state.transforms = state.original_transforms

            state.mode = "lines"

            renpy.clear_line_log()
            update_ast()

    class Remove(Action):
        """
        This action removes the current line from the AST and the script.
        """

        def __call__(self):

            if state.change:
                renpy.scriptedit.remove_line(state.filename, state.linenumber)

            state.tag = None
            state.mode = "lines"

            renpy.clear_line_log()
            update_ast()

init 100 python hide in director:

    if button:
        config.overlay_screens.append("director_button")

    for name, file, _line in renpy.dump.transforms:
        if file.startswith("renpy/common/"):
            continue

        if file == "game/screens.rpy":
            continue

        transforms.append(name)
        transforms.sort()


# Styles and screens ###########################################################

style director_frame is _frame:
    xfill True
    yfill False
    background "#d0d0d0d0"
    ypadding 0
    yalign 0.0

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

style director_statement_text is director_text

style director_statement_button is director_button

style director_statement_button_text is director_button_text:
    size 22


screen director_lines(state):

    frame:
        style "empty"
        background Solid("#fff8", xsize=20, xpos=189)

        has vbox:
            xfill True

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

    $ kind = state.kind or "(statement)"
    $ tag = state.tag or "(tag)"
    $ attributes =  " ".join(director.get_ordered_attributes()) or "(attributes)"
    $ transforms = ", ".join(state.transforms) or "(transform)"

    hbox:
        style_prefix "director_statement"

        textbutton "[kind] " action SetField(state, "mode", "kind")
        textbutton "[tag] " action SetField(state, "mode", "tag")
        textbutton "[attributes] " action SetField(state, "mode", "attributes")
        text "at "
        textbutton "[transforms]" action SetField(state, "mode", "transform")

    null height 14


screen director_footer(state):

    null height 14


    hbox:
        style_prefix "director_action"

        spacing 26

        if state.change:
            textbutton "Change" action director.Commit()
        else:
            textbutton "Add" action director.Commit()


        textbutton "Cancel" action director.Cancel()

        if state.change:
            textbutton "Remove" action director.Remove()

screen director_kind(state):

    vbox:
        xfill True

        use director_statement(state)

        text "Statement:" size 20

        frame:
            style "empty"
            left_margin 10

            hbox:

                box_wrap True
                spacing 20

                textbutton "scene" action director.SetKind("scene")
                textbutton "show" action director.SetKind("show")
                # textbutton "with" action SetKind("with")

        use director_footer(state)


screen director_tag(state):

    vbox:
        xfill True

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
        xfill True

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


screen director_attributes(state):

    vbox:
        xfill True

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


screen director_transform(state):

    vbox:
        xfill True

        use director_statement(state)

        text "Transforms:"

        frame:
            style "empty"
            left_margin 10

            hbox:
                box_wrap True
                spacing 20

                for t in director.get_transforms():
                    textbutton "[t]":
                        action director.ToggleTransform(t)
                        alternate director.AddTransform(t)
                        style "director_button"
                        ypadding 0

        use director_footer(state)


screen director():
    modal True
    zorder 99

    $ state = director.state

    frame:
        style_prefix "director"

        has fixed:
            fit_first True

        if state.mode == "lines":
            use director_lines(state)
        elif state.mode == "kind":
            use director_kind(state)
        elif state.mode == "tag":
            use director_tag(state)
        elif state.mode == "attributes":
            use director_attributes(state)
        elif state.mode == "transform":
            use director_transform(state)

        if not director.commercial:
            text "The interactive director is licensed for non-commercial use only.":
                xalign 1.0
                yalign 1.0
                size 10


screen director_button():

    # Ensure this appears on top of other screens.
    zorder 100

    textbutton _("Director"):
        style "director_launch_button"
        action director.Start()

style director_launch_button is quick_button:
    xalign 0.9
    yalign 1.0

style director_launch_button_text is quick_button_text

