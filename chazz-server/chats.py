

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
        msg = author.name + ' said: ' + msg
        recipients = self.participants[:]
        recipients.remove(author)
        return msg, recipients
