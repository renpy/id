init python in director:
    from store import Action, config
    import store

    state = renpy.session.get("director", None)
    if state is None:

        state = store.NoRollback()

        # Is the directory currently active.
        state.active = False

        renpy.session["director"] = state



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
