from flask import Flask, jsonify, request
from server.state_machine import StateMachine, LoginException
from server.user_manage import UserManage

app = Flask(__name__)
user_manage = UserManage()
with open("config.txt", "r") as f:
    state_machine = StateMachine(list(map(lambda string: string.strip(), f.readlines())))


@app.route('/')
def connect():
    user, token = user_manage.connect()
    return jsonify({"msg": state_machine.hello(user.state), "token": token}), 200


@app.route('/send')
def send():
    try:
        msg = request.args.get("msg")
        token = request.args.get("token")
        user = user_manage.jwt_decode(token)
        response = state_machine.condition_transform(user.state, msg)
        return jsonify(response), 200
    except KeyError:
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
    except (KeyError, ValueError):
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
    except KeyError:
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
    except KeyError:
        return "ParameterError", 400


if __name__ == '__main__':
    app.run(threading=True)
