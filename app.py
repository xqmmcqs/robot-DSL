from flask import Flask, jsonify, request
from state_machine import UserState, StateMachine, LoginException
import jwt
import time
from threading import Timer, Lock


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
        username = jwt.decode(token, self.key, algorithms="HS256").get("username")
        if username is None or username not in self.users.keys():
            raise jwt.InvalidTokenError
        return self.users[username]

    def connect(self):
        username = f"Guest_{time.time_ns()}"
        with self.lock:
            self.users[username] = User(username)
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


app = Flask(__name__)
user_manage = UserManage()
with open("config.txt", "r") as f:
    state_machine = StateMachine(list(map(lambda string: string.strip(), f.readlines())))


@app.route('/')
def connect():
    user, token = user_manage.connect()
    user.timer = Timer(300, user_manage.timeout_handler, user.username)
    return jsonify({"msg": state_machine.hello(user.state), "token": token}), 200


@app.route('/send')
def send():
    try:
        msg = request.args.get("msg")
        token = request.args.get("token")
        user = user_manage.jwt_decode(token)
        response = state_machine.condition_transform(user.state, msg)
        return jsonify(response), 200
    except (KeyError, jwt.InvalidTokenError):
        return "ParameterError", 400
    except LoginException:
        return "NeedLogin", 401


@app.route('/echo')
def echo():
    try:
        seconds = int(request.args.get("seconds"))
        token = request.args.get("token")
        user = user_manage.jwt_decode(token)
        response = state_machine.timeout_transform(user.state, seconds)
        return jsonify(response), 200
    except (KeyError, jwt.InvalidTokenError, ValueError):
        return "ParameterError", 400
    except LoginException:
        return "NeedLogin", 401


@app.route('/login')
def login():
    try:
        username = request.args.get("username")
        passwd = request.args.get("passwd")
        token = request.args.get("token")
        user = user_manage.jwt_decode(token)
        new_token = user_manage.login(user, username, passwd)
        return jsonify(new_token), 200
    except (KeyError, jwt.InvalidTokenError):
        return "ParameterError", 400


@app.route('/register')
def register():
    try:
        username = request.args.get("username")
        passwd = request.args.get("passwd")
        token = request.args.get("token")
        user = user_manage.jwt_decode(token)
        new_token = user_manage.register(user, username, passwd)
        return jsonify(new_token), 200
    except (KeyError, jwt.InvalidTokenError):
        return "ParameterError", 400


if __name__ == '__main__':
    app.run(threading=True)
