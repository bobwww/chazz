class Chat:

    def __init__(self, id, name, participants=None):
        self.id = id
        self.name = name
        if participants is None:
            participants = []
        self.participants = participants

    def add_participant(self, user):
        self.participants.append(user)

    def remove_participant(self, user):
        self.participants.remove(user)

    def handle_new_msg(self, msg, author):
        msg = author.prefix + author.name + ' said: ' + msg
        recipients = self.participants[:]
        recipients.remove(author)
        return msg, recipients

    def get_oldest_user(self):
        if not self.participants:
            return
        oldest_user = self.participants[0]
        min = oldest_user.get_age()
        for user in self.participants:
            if user.get_age() < min:
                oldest_user = user
                min = oldest_user.get_age()
        return oldest_user

    def is_any_admin(self):
        for user in self.participants:
            if user.is_admin():
                return True
        return False
