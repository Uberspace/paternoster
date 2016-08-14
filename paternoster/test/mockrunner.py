class MockRunner:
    def __init__(self, result=True):
        self._result = result

    def run(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self._result
