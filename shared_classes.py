from uuid     import UUID
from datetime import datetime


class Contact:
    def __init__(self, uuid:UUID|str, name:str, last_seen:str|datetime, is_online:bool, color:str):
        self.uuid = uuid if type(uuid) == UUID else UUID(uuid)
        self.name = name
        self.is_online = is_online
        self.color = color
        if type(last_seen) == datetime: last_seen = str(last_seen).split('.')[0]
        elif last_seen and '.' in last_seen: last_seen = last_seen.split('.')[0]
        self.last_seen = last_seen

    def __repr__(self):
        return f'({self.name}, {self.is_online}, {self.last_seen}, {self.color})'

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __hash__(self):
        return hash(self.uuid)


class Request:
    def __init__(self, uuid_from:UUID|str, uuid_to:UUID|str, name_from:str = None, name_to:str = None):
        self.uuid_from = uuid_from if type(uuid_from) == UUID else UUID(uuid_from)
        self.uuid_to   = uuid_to   if type(uuid_to  ) == UUID else UUID(uuid_to  )
        self.name_from = name_from
        self.name_to   = name_to


class Message:
    def __init__(self, uuid:UUID|str, uuid_from:UUID|str, uuid_to:UUID|str, text:str, image:bytes, date:str|datetime):
        self.uuid  = uuid if type(uuid) == UUID else UUID(uuid)
        self.uuid_from = uuid_from if type(uuid_from) == UUID else UUID(uuid_from)
        self.uuid_to   = uuid_to   if type(uuid_to  ) == UUID else UUID(uuid_to  )
        self.text  = text
        self.image = image
        if type(date) == datetime: date = str(date).split('.')[0]
        elif date and '.' in date: date = date.split('.')[0]
        self.date  = date