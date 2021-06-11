import random
import time
counter = 0


class Guest:

    def __init__(self, uid, name, age):
        self._name = name
        self._uid = uid
        self._age = age
        self.admin = False
        self.muted = False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def prefix(self):
        prefix = ''
        if self.is_admin():
            prefix = '[ADMIN]'
        return prefix

    def is_admin(self):
        return self.admin

    def is_muted(self):
        return self.muted

    def set_admin(self, is_admin: bool):
        self.admin = is_admin

    def get_age(self):
        return self._age

    def set_age(self, new_time):
        self._age = new_time

    @property
    def uid(self):
        return self._uid

def name_to_user(name, users):
    for user in users:
        if user.name == name:
            return user


def is_name_valid(name: str):
    return name.isalnum() and name[0].isalpha() and len(name) <= 16
    # Name must start with a letter. Name must contain only letters and numbers. Name must not exceed 16 characters.

def is_name_in_use(name, users=()):
    used_names = [u.name for u in users]
    return name in users

def create_guest(users=()):
    global counter

    used_names = [u.name for u in users]

    with open('name_list.txt', 'r') as fd:
        text = fd.readline()
    names = text.split(',')
    name = ''
    for i in range(len(names)):
        name = names[i]
        if name not in used_names:
            break
    uid = counter
    counter += 1
    age = time.time()
    return Guest(uid, name, age)
