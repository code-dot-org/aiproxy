class AnyStringWith(str):
    """ Matches a substring of a string argument.
    """

    def __eq__(self, other):
        return self in other


