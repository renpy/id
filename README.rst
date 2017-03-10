Ren'Py Interactive Director
===========================

The Ren'Py interactive director is meant to help you direct a script. It
isn't meant as a replacement for the text editor, which is required to add
most statements. The director lets you add - with a live preview - scene,
show, hide and with statements, directing image presentation.

Note that this is not an open source project. It is free for non-commercial
use. Please see the full license below for more details.

Download and Demo
-----------------

To try the demo, download the latest version available from:

   https://www.renpy.org/dl/id/

Unzip the file, and place it into either your Ren'Py SDK directory,
or your projects directory. After restarting the Ren'Py launcher,
the id project will be on your list of projects. Click it, launch
the game, and it should walk you through a basic demo.

Usage
-----

To use the director in your own project, copy game/id.rpy into your own
project's game directory.

When you run the game, an "Interactive Director" button will appear
at the top of the screen. Clicking it will bring up the director window.

By default, the director window shows a list of lines that ran before the
current line. Click outside the lines window to advance the script, or
rollback outside it to roll back. Click the + between a lines to add a line, or the ✎ before a
line to edit that line. (Only scene, show, hide, and with statements can
currently be added to the script or edited.)

When editing a line, the statement type can be selected, along with
appropriate parameters. Choose "Add" to add the new line, "Change" to change
an existing line, "Cancel" to cancel editing, and "Remove" to remove an
existing line.

Click "Done" when finished editing.

Variables
---------

There are a number of variables defined in the director namespace that control
how the interactive director functions. These may be either updated using
python code, or hidden using the define statement.

``director.tag_blacklist = { "black", "text", "vtext" }``
    A blacklist of tags that will not be shown for the show, scene, or hide
    statements.

``director.scene_tags = { "bg" }``
    The set of tags that will be presented for the scene statement, and hidden
    from the show statement.

``director.show_tags = set()``
    If not empty, only the tags present in this set will be presented for the
    show statement.

``director.transforms = [ "left", "center", "right" ]``
    A list of transforms that will be presented as part of the editor.
    In addition to these, any transform defined using the transform
    statement outside of common code will be added to the list of
    transforms, which is then sorted.

``director.transitions = [ "dissolve", "pixellate" ]``
    A list of transitions that are available to the with statement. Since
    transitions can't be auto-detected, these must be added manually.

``director.button = True``
    If True, the director displays a screen with a button to access the
    director window. If False, the game can provide it's own access, by
    making available the director.Start action.

``director.spacing = 1``
    The spacing between a director (scene, show, hide, with, play, queue, and voice) line
    and a non-director line, or vice versa. These spacings should be 0 or 1 lines, a higher spacing
    may not work.

``director.director_spacing = 0``
    The spacing between two consecutive director lines.

``director.other_spacing = 0``
    The spacing between two consecutive non-director lines.

``director.source_height = 280``
    The spacing of the list of source code lines in the director. (This is
    just the lines themselves, not the buttons.)

The director can also be customized by editing its styles.

Custom Director Button
----------------------

When director.button is true, the director_button screen is displayed to
provide access to your game. This screen can be replaced to customize
the button. An example replacement is::

    screen director_button:
        zorder 100

        textbutton "Interactive Director":
            action director.Start()
            xalign 1.0
            yalign 0.0

License
-------

This program is free for *non-commercial use*, under the terms of the
following license::

    # Permission to use, copy, modify, and/or distribute this software for
    # non-commerical purposes is hereby granted, provided that the above
    # copyright notice and this permission notice appear in all copies.
    #
    # For the purpose of this license, when using this software to develop a
    # another software program, this program is being used commercially if
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

While being developed in the open, this tool is not open source. It's
free for use in creating non-commercial games, but is commercial when
used to develop commercial games.

I haven't figured out the commercial terms yet, but you should expect them
to be quite nominal. Email pytom@bishoujo.us if you really want to use
this code to make a commercial game.


Changelog
---------

3.0
    This release supports screen language statements that do not not have
    an associated image. It also determines if a scene, show, or hide
    statement is not editable, and makes the button insensitive if that
    is the case.

2.0
    This release required Ren'Py 6.99.12.3 to run. It adds support for
    the behind clause, adds the director.show_tags set, and adds some
    basic support for attribute images.

1.0
    This was the initial release.
