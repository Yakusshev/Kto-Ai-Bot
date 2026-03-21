from dataclasses import dataclass


@dataclass(frozen = True)
class UserModel:
    id: int
    username: str
    first_name: str
    last_name: str
    business_connection_id: str
