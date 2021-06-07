import random

counter = 0


class Guest:

    def __init__(self, uid, name):
        self._name = name
        self._uid = uid
        self.admin = True
        self.muted = False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    def is_admin(self):
        return self.admin

    def is_muted(self):
        return self.muted

    def set_admin(self, is_admin: bool):
        self.admin = is_admin

    @property
    def uid(self):
        return self._uid


def create_guest():
    global counter

    with open('name_list.txt', 'r') as fd:
        text = fd.readline()
    names = text.split(',')
    name = random.choice(names)
    uid = counter
    counter += 1
    return Guest(uid, name)
