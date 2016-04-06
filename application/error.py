

class CaseworkFrontEndError(Exception):
    def __init__(self, value):
        self.value = value
        super(CaseworkFrontEndError, self).__init__(value)

    def __str__(self):
        return self.value