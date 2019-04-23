from P4 import P4,P4Exception

class Repo():
    def __init__(self, port=None, user=None):
        self.p4 = P4()
        if port:
            self.p4.port = port
        if user:
            self.p4.user = user            
        self.p4.connect()

    def info(self):
        return self.p4.run_info()[0]

