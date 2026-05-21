class AcademyStorage:
    def __init__(self):
        self.traces = []
        self.budgets = {}
        self.spends = {}
        self.datasets = []

_storage = AcademyStorage()

def get_academy_storage() -> AcademyStorage:
    return _storage
