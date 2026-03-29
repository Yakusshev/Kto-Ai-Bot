from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen = True)
class BirthdateModel:
    day: int
    month: int
    year: int | None

@dataclass(frozen = True)
class UserModel:
    id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    bio: str | None
    birthdate: BirthdateModel | None
    business_connection_id: str | None
    update_date: datetime | None
    channel_title: str | None
    channel_username: str | None
    channel_id: int | None

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name