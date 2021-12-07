from flask import Flask, jsonify, request, abort

app = Flask(__name__)

state = 0
message_set = [["您好", "输入 余额 以查看余额，输入 退出 以退出"], ["您的余额为0", "输入 退出 以退出，输入 返回 以返回主菜单"], []]
user = "Guest"
user_set = {"Guest": ""}


@app.route('/')
def connect():
    token = "Guest"
    global state
    state = 0
    return jsonify({"msg": message_set[0], "token": token}), 200


@app.route('/send')
def send():
    try:
        msg = request.args["msg"]
        token = request.args["token"]
        global state, user
        if token != user:
            abort(403)
        if msg == "余额":
            if state == 0:
                if user == "Guest":
                    abort(401)
                state = 1
        elif msg == "返回":
            if state == 1:
                state = 0
        elif msg == "退出":
            state = -1
        return jsonify({"msg": message_set[state], "exit": state == -1}), 200
    except KeyError:
        abort(400)


@app.route('/echo')
def echo():
    try:
        seconds = int(request.args["seconds"])
        token = request.args["token"]
        global state, user
        if token != user:
            abort(403)
        if seconds >= 60:
            state = -1
        return jsonify({"msg": [], "exit": state == -1, "reset": False}), 200
    except (KeyError, ValueError):
        abort(400)


@app.route('/login')
def login():
    try:
        username = request.args["username"]
        passwd = request.args["passwd"]
        token = request.args["token"]
        global user
        if token != user:
            abort(403)
        if username in user_set and username != "Guest" and passwd == user_set[username]:
            user = username
        else:
            username = None
        return jsonify({"token": username}), 200
    except KeyError:
        abort(400)


@app.route('/register')
def register():
    try:
        username = request.args["username"]
        passwd = request.args["passwd"]
        token = request.args["token"]
        global user
        if token != user:
            abort(403)
        if username not in user_set:
            user = username
            user_set[username] = passwd
        else:
            username = None
        return jsonify({"token": username}), 200
    except KeyError:
        abort(400)


if __name__ == '__main__':
    app.run(threading=True)
