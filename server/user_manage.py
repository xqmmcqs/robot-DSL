from server.state_machine import UserState
import jwt
from threading import Lock, Timer
import time


class User:
    def __init__(self, username):
        self.state = UserState()
        self.username = username


class UserManage:
    def __init__(self, key="this_is_a_secret"):
        self.users = dict()
        self.lock = Lock()
        self.key = key

    def jwt_encode(self, username):
        return jwt.encode({"username": username}, self.key, algorithm="HS256")

    def jwt_decode(self, token):
        try:
            username = jwt.decode(token, self.key, algorithms="HS256").get("username")
            if username is None or username not in self.users.keys():
                raise jwt.InvalidTokenError
            return self.users[username]
        except jwt.InvalidTokenError:
            raise KeyError

    def connect(self):
        username = f"Guest_{time.time_ns()}"
        with self.lock:
            self.users[username] = User(username)
            self.users[username].timer = Timer(300, self.timeout_handler, username)
        return self.users[username], self.jwt_encode(username)

    def login(self, user: User, username, passwd):
        old_username = user.username
        if not self.users[old_username].state.login(username, passwd):
            return None
        with self.lock:
            self.users[username] = self.users[old_username]
            self.users[username].username = username
            del self.users[old_username]
        return self.jwt_encode(username)

    def register(self, user: User, username, passwd):
        old_username = user.username
        if not self.users[old_username].state.register(username, passwd):
            return None
        with self.lock:
            self.users[username] = self.users[old_username]
            self.users[username].username = username
            del self.users[old_username]
        return self.jwt_encode(username)

    def timeout_handler(self, username):
        with self.lock:
            del self.users[username]
