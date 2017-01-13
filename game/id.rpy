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

    # The version of the director.
    version = "0.1"

    # Is the director licensed for commercial use? Yes, you can remove
    # the warning by changing this variable - but it doesn't change the
    # license of the director tool.
    commercial = False

    # A set of tags that will not be show to the user.
    tag_blacklist = { "black", "text", "vtext" }

    # A set of tags that should only be used with the scene statement.
    scene_tags = { "bg" }

    # A list of transforms to use.
    transforms = [ "left", "center", "right" ]

    # A list of transitions to use.
    transitions = [ "dissolve", "pixellate" ]

    # Should we offer a button to access the director?
    button = True

    # The spacing between a non-display line and a display line, or vice
    # versa.
    spacing = 1

    # The spacing between two display lines.
    display_spacing = 0

    # The spacing between two non-display lines.
    other_spacing = 0

    # The maximum height of the source code list.
    source_height = 280

    state = renpy.session.get("director", None)

    # A list of statements we find too uninteresting to present to the
    # creator.
    UNINTERESTING_NODES = (
        renpy.ast.Translate,
        renpy.ast.EndTranslate,
    )

    DISPLAY_NODES = (
        renpy.ast.Show,
        renpy.ast.Hide,
        renpy.ast.Scene,
        renpy.ast.With,
    )

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

        # What tags are currently showing?
        state.showing = set()

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

    def interact_base():
        """
        This is called by interact to update our data structures.
        """

        if renpy.game.interface.trans_pause:
            return False

        show_director = False

        # Update the line log.
        lines = renpy.get_line_log()
        renpy.clear_line_log()

        # Update state.line to the current line.
        state.line = renpy.get_filename_line()

        # State.lines is the list of lines we've just seen, along with
        # the actions used to edit those lines.
        for lle in lines[-30:]:
            if isinstance(lle.node, renpy.ast.Say):
                state.lines = [ ]
                break

        for lle in lines[-30:]:

            filename = lle.filename
            line = lle.line
            node = lle.node

            if isinstance(node, UNINTERESTING_NODES):
                continue

            if filename.startswith("renpy/"):
                show_director = False
                continue
            else:
                show_director = True

            text = renpy.scriptedit.get_line_text(filename, line)

            if text is None:
                text = ""

            text = text.strip()

            short_fn = filename.rpartition('/')[2]
            pos = "{}:{:04d}".format(short_fn, line)

            if lle.abnormal:
                add_action = None
            else:
                add_action = AddStatement(lle)

            if isinstance(node, DISPLAY_NODES):
                change_action = ChangeStatement(lle, node)
            else:
                change_action = None

            state.lines.append((
                pos,
                text,
                add_action,
                change_action,
            ))

        return show_director


    def interact():
        """
        This is called once per interaction, to update the list of lines
        being displayed, and also to show or hide the director as appropriate.
        """

        show_director = interact_base()

        # Show the director screen.
        if show_director and state.show_director and (renpy.context_nesting_level() == 0):
            if not renpy.get_screen("director"):
                renpy.show_screen("director")
        else:
            if renpy.get_screen("director"):
                renpy.hide_screen("director")

    def line_log_callback(lle):
        """
        This annotates a line log entry with more information.
        """
        lle.showing = set(renpy.get_showing_tags())


    def init():
        """
        This is called once at game start, to reconfigured Ren'Py to
        support the ID.
        """

        config.clear_lines = False
        config.line_log = True
        config.line_log_callbacks = [ line_log_callback ]

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

        if state.kind == "with":
            return "with {}".format(state.transition)

        if state.tag is None:
            return None

        if state.kind == "hide":

            attributes = state.attributes

        else:

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

        if state.kind == "hide":
            return

        state.mode = "attributes"



    def find_statement(filename, line, delta, limit=10):
        """
        Tries to find a statement near `line`. If it can't find it on `line`
        itself, it searches forward (if `delta`) is positive or back (if `delta`)
        is negative.

        Returns the line number and nodes for the statement, or (None, None) if the
        statement is not found after searching `limit` lines.
        """

        for _i in range(limit):

            nodes = renpy.scriptedit.nodes_on_line(filename, line)
            if nodes:
                return line, nodes

            line += delta

        return None, None

    def needs_space(filename, line):
        """
        Returns True if there should be a space between (filename, line-1) and
        (filename, line).
        """


        previous, previous_nodes = find_statement(filename, line-1, -1)

        if previous is None:
            return None

        next, next_nodes = find_statement(filename, line, 1)

        if next is None:
            return None


        def display(nodes):
            for n in nodes:
                if isinstance(n, DISPLAY_NODES):
                    return True

            return False

        previous_display = display(previous_nodes)
        next_display = display(next_nodes)

        if previous_display ^ next_display:
            return spacing
        elif previous_display:
            return display_spacing
        else:
            return other_spacing

    def is_spacing(filename, line):

        line = renpy.scriptedit.get_full_text(filename, line)

        if line is None:
            return False

        return not line.strip()


    def adjust_spacing_before(filename, line):
        """
        Adjusts the spacing between (filename, line) and the line before it.
        """

        line, _ = find_statement(filename, line, 1)

        if line is None:
            return

        space = needs_space(filename, line)

        if space is None:
            return

        previous, _ = find_statement(filename, line - 1, -1)

        blanks = [ ]

        for i in range(previous + 1, line):
            if not is_spacing(filename, i):
                break

            blanks.append(i)

        delta_space = space - len(blanks)

        if delta_space > 0:
            for _ in range(delta_space):
                renpy.scriptedit.adjust_ast_linenumbers(filename, previous + 1, 1)
                renpy.scriptedit.insert_line_before('', filename, previous + 1)

        elif delta_space < 0:
            blanks.reverse()
            blanks = blanks[space:]

            for i in blanks:
                renpy.scriptedit.adjust_ast_linenumbers(filename, i, -1)
                renpy.scriptedit.remove_line(filename, i)


    def add_spacing(filename, line):
        adjust_spacing_before(filename, line + 1)
        adjust_spacing_before(filename, line)

    def remove_spacing(filename, line):
        adjust_spacing_before(filename, line)


    # Screen support functions #################################################

    def get_tags():
        """
        Returns a list of tags that are valid for the current statement kind.
        """

        if state.kind == "scene":
            rv = [ i for i in renpy.get_available_image_tags() if not i.startswith("_") if i not in tag_blacklist if i in scene_tags ]
        elif state.kind == "show":
            rv = [ i for i in renpy.get_available_image_tags() if not i.startswith("_") if i not in tag_blacklist if i not in scene_tags ]
        elif state.kind == "hide":
            rv = [ i for i in renpy.get_available_image_tags() if i in state.showing if not i.startswith("_") if i not in tag_blacklist if i not in scene_tags ]
        else:
            rv = [ ]

        rv.sort(key=component_key)
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
            l.append((attrtotalpos[attr] / attrcount[attr], component_key(attr), attr))

        l.sort()
        return [ i[2] for i in l ]

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

        def __init__(self, lle):
            self.lle = lle

        def __call__(self):

            state.filename = self.lle.filename
            state.linenumber = self.lle.line
            state.showing = self.lle.showing

            state.kind = None
            state.mode = "kind"
            state.tag = None
            state.original_tag = None
            state.attributes = [ ]
            state.original_attributes = [ ]
            state.transforms = [ ]
            state.original_transforms = [ ]
            state.transition = None
            state.original_transition = None

            state.added_statement = None
            state.change = False

            update_ast()

    class ChangeStatement(Action):
        """
        An action that changes the statement at `filename`:`linenumber`.

        `node`
            Should be the AST node corresponding to that statement.
        """

        def __init__(self, lle, node):
            self.lle = lle

            self.tag = None
            self.attributes = [ ]
            self.transforms = [ ]
            self.transition = None

            if isinstance(node, renpy.ast.Show):
                self.kind = "show"

                self.tag = node.imspec[0][0]
                self.attributes = list(node.imspec[0][1:])
                self.transforms = list(node.imspec[3])


            elif isinstance(node, renpy.ast.Scene):
                self.kind = "scene"

                self.tag = node.imspec[0][0]
                self.attributes = list(node.imspec[0][1:])
                self.transforms = list(node.imspec[3])


            elif isinstance(node, renpy.ast.Hide):
                self.kind = "hide"

                self.tag = node.imspec[0][0]
                self.attributes = list(node.imspec[0][1:])
                self.transforms = list(node.imspec[3])

            elif isinstance(node, renpy.ast.With):
                self.kind = "with"
                self.transition = node.expr



        def __call__(self):
            state.filename = self.lle.filename
            state.linenumber = self.lle.line
            state.showing = self.lle.showing

            state.kind = self.kind

            if self.kind == "with":
                state.mode = "with"
            elif self.kind == "hide":
                state.mode = "tag"
            else:
                state.mode = "attributes"

            state.tag = self.tag
            state.attributes = self.attributes
            state.original_tag = self.tag
            state.original_attributes = list(self.attributes)
            state.transforms = list(self.transforms)
            state.original_transforms = list(self.transforms)
            state.transition = self.transition
            state.original_transition = self.transition

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

            if self.kind in ("scene", "show", "hide"):
                state.mode = "tag"
                pick_tag()

            if self.kind == "with":
                state.mode = "with"

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

            if state.kind != "hide":
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

    class SetTransition(Action):
        """
        This sets the transition used by a with statement.
        """

        def __init__(self, transition):
            self.transition = transition

        def __call__(self):
            state.transition = self.transition

            update_ast()

        def get_selected(self):
            return self.transition == state.transition


    class Commit(Action):
        """
        Commits the current statement to the .rpy files.
        """

        def __call__(self):
            statement = get_statement()

            if statement:
                renpy.scriptedit.insert_line_before(statement, state.filename, state.linenumber)

            if state.change:
                if statement:
                    renpy.scriptedit.remove_line(state.filename, state.linenumber + 1)
                else:
                    renpy.scriptedit.remove_line(state.filename, state.linenumber)

            if not state.change and statement:
                add_spacing(state.filename, state.linenumber)

            if state.change and not statement:
                remove_spacing(state.filename, state.linenumber)

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

            state.kind = None
            state.tag = None
            state.mode = "lines"

            renpy.clear_line_log()

            try:
                update_ast()
            finally:
                if state.change:
                    renpy.scriptedit.remove_line(state.filename, state.linenumber)
                    remove_spacing(state.filename, state.linenumber)


    # Displayables #############################################################

    class SemiModal(renpy.Displayable):
        """
        This wraps a displayable, and ignores
        """

        def __init__(self, child):
            renpy.Displayable.__init__(self)

            self.child = child
            self.w = 0
            self.h = 0

        def render(self, width, height, st, at):
            surf = renpy.render(self.child, width, height, st, at)
            w, h = surf.get_size()

            self.w = w
            self.h = h

            rv = renpy.Render(w, h)
            rv.blit(surf, (0, 0))

            return rv

        def event(self, ev, x, y, st):

            rv = self.child.event(ev, x, y, st)
            if rv is not None:
                return rv

            if state.mode != "lines":

                if renpy.map_event(ev, "rollback") or renpy.map_event(ev, "rollforward"):
                    raise renpy.IgnoreEvent()

                raise renpy.display.layout.IgnoreLayers()

            if (0 <= x < self.w) and (0 <= y < self.h):
                raise renpy.display.layout.IgnoreLayers()

            return None

        def get_placement(self):
            return self.child.get_placement()

        def visit(self):
            return [ self.child ]

    # Sort #####################################################################

    import re

    def component_key(s):
        """
        Sorts l in a way that groups numbers together and treats them as
        numbers (so c10 comes after c9, not c1.)
        """
        rv = [ ]

        for i, v in enumerate(re.split(r'(\d+)', s.lower())):
            if not v:
                continue

            if i & 1:
                v = int(v)

            rv.append(v)

        return tuple(rv)

init 100 python hide in director:

    if button:
        config.overlay_screens.append("director_button")

    for name, file, _line in renpy.dump.transforms:
        if file.startswith("renpy/common/"):
            continue

        if file == "game/screens.rpy":
            continue

        transforms.append(name)
        transforms.sort(key=component_key)


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

style director_vscrollbar is _vscrollbar


screen director_lines(state):

    frame:
        style "empty"
        background Solid("#fff8", xsize=20, xpos=189)

        has vbox:
            xfill True

        viewport:
            scrollbars "vertical"
            ymaximum director.source_height
            mousewheel True
            yinitial 1.0
            yfill False

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

        if state.attributes or state.kind in { "scene", "show"}:
            textbutton "[attributes] " action SetField(state, "mode", "attributes")

        if state.transforms or state.kind in { "scene", "show"}:
            text "at "
            textbutton "[transforms]" action SetField(state, "mode", "transform")

    null height 14

screen director_with_statement(state):

    $ transition = state.transition or "(transition)"

    hbox:
        style_prefix "director_statement"

        text "with "
        textbutton "[transition]" action SetField(state, "mode", "with")

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
                textbutton "hide" action director.SetKind("hide")
                textbutton "with" action director.SetKind("with")

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

screen director_with(state):

    vbox:
        xfill True

        use director_with_statement(state)

        text "Transition:"

        frame:
            style "empty"
            left_margin 10

            hbox:
                box_wrap True
                spacing 20

                for t in director.transitions:
                    textbutton "[t]":
                        action director.SetTransition(t)
                        style "director_button"
                        ypadding 0

        use director_footer(state)


screen director():
    zorder 99

    $ state = director.state

    if renpy.loadable("id/" + state.mode + ".png"):
        add ("id/" + state.mode + ".png")

    frame:
        style_prefix "director"
        at director.SemiModal

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
        elif state.mode == "with":
            use director_with(state)


        hbox:
            xalign 1.0
            yalign 1.0
            spacing 10

            if not director.commercial:
                text "v[director.version]":
                    size 10

                text "The interactive director is licensed for non-commercial use only.":
                    size 10


screen director_button():

    # Ensure this appears on top of other screens.
    zorder 100

    if not (director.state.active and director.state.show_director):
        textbutton _("Interactive Director"):
            style "director_launch_button"
            action director.Start()

style director_launch_button is quick_button:
    xalign 0.5
    yalign 0.0
    xpadding 50
    bottom_padding 10

style director_launch_button_text is quick_button_text

