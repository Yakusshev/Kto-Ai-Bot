import threading

from bot.feature.business.domain.model.SaveMessageModel import OwnerModel


class LocalDataSource:

    __instance = None
    __lock = threading.Lock()

    owner: OwnerModel | None = None

    def __new__(cls):
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    cls.__instance = super().__new__(cls)
        return cls.__instance

    def set_owner(self, owner: OwnerModel):
        self.owner = owner

    def get_owner(self):
        return self.owner

