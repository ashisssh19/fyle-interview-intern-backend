class FyleError(Exception):

    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self):
        res = dict()
        res['message'] = self.message
        return res
