Ren'Py Interactive Director
===========================

The Ren'Py interactive director is meant to help you direct a script. It
isn't meant as a replacement for the text editor, which is required to add
most statements. The director lets you add - with a live preview - scene,
show, hide and with statements, directing image presentation.

The Interactive Director is now an open source project, licensed under
the same MIT license as Ren'Py itself.

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


Scene, Show, and Hide
^^^^^^^^^^^^^^^^^^^^^

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

With
^^^^

``director.transitions = [ "dissolve", "pixellate" ]``
    A list of transitions that are available to the with statement. Since
    transitions can't be auto-detected, these must be added manually.

Play, Queue, Stop, and Voice
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``director.audio_channels = [ "music", "sound", "audio" ]``
    The name of the audio channels that can be used with the play, show
    and stop statements.

``director.voice_channel = "voice"``
    The name of the audio channel used by voice.

``director.audio_patterns = [ "*.opus", "*.ogg", "*.mp3" ]``
    The default list of audio patterns that are used to match the files
    available in an audio channel.

``director.audio_channel_patterns = { }``
    A map from a channel name to the list of audio patterns that are
    available in that audio channel. For example, if this is set to
    ``{ 'sound' : [ 'sound/*.opus' ], 'music' : [ 'music/*.opus' ] }`` the
    music and sound channels get their own lists of patterns.

Access
^^^^^^

``director.button = True``
    If True, the director displays a screen with a button to access the
    director window. If False, the game can provide it's own access, by
    making available the director.Start action.

Line Spacing
^^^^^^^^^^^^

``director.spacing = 1``
    The spacing between a director (scene, show, hide, with, play, queue, and voice) line
    and a non-director line, or vice versa. These spacings should be 0 or 1 lines, a higher spacing
    may not work.

``director.director_spacing = 0``
    The spacing between two consecutive director lines.

``director.other_spacing = 0``
    The spacing between two consecutive non-director lines.

Viewport
^^^^^^^^

``director.viewport_height = 280``
    The maximum height of scrolling viewports used by the director.

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


Audio Filename Functions
------------------------

There are a number of audio filename functions that can be used to convert
filenames on disk to filenames in code. This can be used to match Ren'Py
functionality that maps filenames. For example, if one has::

    define config.voice_filename_format = "v/{filename}.ogg"

one can define the functions::

    init python in director:

        def audio_code_to_filename(channel, code):
            """
            This converts the name of an audio filename as seen in the code,
            to the filename as seen on disk.
            """

            if channel == "voice":
                return "v/" + code + ".ogg"

            return code

        def audio_filename_to_code(channel, fn):
            """
            This converts the name of an audio filename on disk to the filename
            as seen in code.
            """

            if channel == "voice":
                return fn.replace("v/", "").replace(".ogg", "")

            return fn

        def audio_filename_to_display(channel, fn):
            """
            This converts the audio filename as seen on disk so it can be
            presented to the creator.
            """

            if channel == "voice":
                return fn.replace("v/", "").replace(".ogg", "")

            return fn

to match it.


License
-------

This program is free for all purposes - commercial and non-commercial,
under the terms of the following license::

    # Permission is hereby granted, free of charge, to any person
    # obtaining a copy of this software and associated documentation files
    # (the "Software"), to deal in the Software without restriction,
    # including without limitation the rights to use, copy, modify, merge,
    # publish, distribute, sublicense, and/or sell copies of the Software,
    # and to permit persons to whom the Software is furnished to do so,
    # subject to the following conditions:
    #
    # The above copyright notice and this permission notice shall be
    # included in all copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    # EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    # MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    # NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
    # LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    # OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
    # WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


Changelog
---------

4.0
    This release adds support for the play, queue, stop, and voice
    statements, which control sound, music, and voice. Several of the
    configuration variables have been renamed to reflect the fact that not
    all statements are display-related. Automated tests have been added to
    the project, and some bugs have been fixed.

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
