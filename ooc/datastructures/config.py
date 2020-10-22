class Config:
    """Put configurable options here."""

    # detect and remove unreachable commands after each unfold, requires many SMT calls
    remove_unreachable_commands: bool

    # location is considered eliminable if all pairs of ingoing/outgoing commands have at least one unlabeled transition
    elim_must_not_add_new_labels: bool

    @classmethod
    def default(cls):
        config = Config()
        config.remove_unreachable_commands = False
        config.elim_must_not_add_new_labels = False
        return config
