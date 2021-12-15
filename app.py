"""客服系统后端API。

Copyright (c) 2021 Ziheng Mao.
"""

import os
import sys
import jwt
import json
from flask import Flask, jsonify, request, abort
from server.state_machine import StateMachine, LoginError, GrammarError, init_database
from server.user_manage import UserManage

app = Flask(__name__)
try:
    current_path = os.path.split(os.path.realpath(__file__))[0]
    config: dict = json.load(open(os.path.join(current_path, "config.json")))
    user_manage = UserManage(config["key"])
    init_database(os.path.join(current_path, config["db_path"]))
    state_machine = StateMachine([os.path.join(current_path, path) for path in config["source"]])
except GrammarError as err:
    print(" ".join(err.context))
    print("GrammarError: ", err.msg)
    sys.exit(1)
except (FileNotFoundError, json.JSONDecodeError, KeyError):
    print("Error with config.json or file not found")
    sys.exit(1)


@app.route('/')
def connect():
    """一个新的客户端连接到服务器时，请求一个token。

    :return: 返回一个消息列表和token，格式为：``{"msg": ["xxx", "xxx"], "token": "xxx"}``。
    :status 200: 成功建立会话。

    一个客户端与服务器建立连接时，或者客户端开始一个新的会话时，从此路由获取一个token。
    服务器默认分配一个访客账户，如果设置了默认的问候消息，还会返回消息列表。
    """
    user, token = user_manage.connect()
    return jsonify({"msg": state_machine.hello(user.state), "token": token}), 200


@app.route('/send')
def send():
    """客户端发送一条新消息，服务器返回响应。

    :param: 客户端发送一条消息和token，格式为：``{"msg": "xxx", "token": "xxx"}``。
    :return: 返回一个消息列表和是否结束会话的标志，格式为：``{"msg": ["xxx", "xxx"], "exit": false}``。
    :status 200: 鉴权成功，服务器产生响应。
    :status 400: 客户端请求消息格式有误。
    :status 403: 鉴权失败。
    :status 401: 用户是访客，需要登录。

    一个客户端通过此路由向服务器发送一条消息。

    收到消息后，服务器首先对token进行鉴权，之后对消息进行处理并产生响应，返回一个消息列表。
    如果服务器需要终止一个会话，则设 ``exit`` 为1，该token立即过期，客户端需要重新开启一个会话。
    """
    try:
        msg = request.args["msg"]
        token = request.args["token"]
        user = user_manage.jwt_decode(token)
        response = state_machine.condition_transform(user.state, msg)
        if user.state.state == -1:
            user_manage.timeout_handler(user.username)
        return jsonify({"msg": response, "exit": user.state.state == -1}), 200
    except KeyError:
        abort(400)
    except jwt.InvalidTokenError:
        abort(403)
    except LoginError:
        abort(401)


@app.route('/echo')
def echo():
    """客户端发送一条echo，服务器返回响应。

    :param: 客户端发送闲置时间和token，格式为：``{"seconds": 5, "token": "xxx"}``。
    :return: 返回一个消息列表、是否结束会话的标志和是否要求用户重置计时器的标志，格式为：
        ``{"msg": ["xxx", "xxx"], "exit": false, reset: false}``。
    :status 200: 鉴权成功，服务器产生响应。
    :status 400: 客户端请求消息格式有误。
    :status 403: 鉴权失败。
    :status 401: 用户是访客，需要登录。

    一个客户端通过此路由向服务器发送一条echo，表明自己仍然存活和用户闲置的时间。

    收到echo后，服务器首先对token进行鉴权，之后依照闲置时间进行处理并产生响应，返回一个消息列表。
    如果服务器需要终止一个会话，则设 ``exit`` 为1，该token立即过期，客户端需要重新开启一个会话。
    如果服务器要求客户端重置闲置时间计时器，则设 ``reset`` 为1，客户端应当重启计时器。
    """
    try:
        seconds = int(request.args["seconds"])
        token = request.args["token"]
        user = user_manage.jwt_decode(token)
        response, exit_, reset_timer = state_machine.timeout_transform(user.state, seconds)
        if exit_:
            user_manage.timeout_handler(user.username)
        return jsonify({"msg": response, "exit": exit_, "reset": reset_timer}), 200
    except (KeyError, ValueError):
        abort(400)
    except jwt.InvalidTokenError:
        abort(403)
    except LoginError:
        abort(401)


@app.route('/login')
def login():
    """客户端请求登录，服务器返回新的token。

    :param: 客户端发送用户名、密码和token，格式为：``{"username": "xxx", "passwd": xxx, "token": "xxx"}``。
    :return: 返回一个新的token，格式为：``{"token": "xxx"}``。
    :status 200: 鉴权并登录成功。
    :status 400: 客户端请求消息格式有误。
    :status 403: 鉴权失败。

    一个客户端通过此路由向服务器发送一个登录请求。

    收到请求后，服务器首先对token进行鉴权，之后验证用户名和密码，如果验证通过，则返回一个新的token。
    原有的token立即过期，客户端需要使用新的token继续会话。
    """
    try:
        username = request.args["username"]
        passwd = request.args["passwd"]
        token = request.args["token"]
        user = user_manage.jwt_decode(token)
        new_token = user_manage.login(user, username, passwd)
        return jsonify({"token": new_token}), 200
    except jwt.InvalidTokenError:
        abort(403)
    except KeyError:
        abort(400)


@app.route('/register')
def register():
    """客户端请求注册，服务器返回新的token。

    :param: 客户端发送用户名、密码和token，格式为：``{"username": "xxx", "passwd": xxx, "token": "xxx"}``。
    :return: 返回一个新的token，格式为：``{"token": "xxx"}``。
    :status 200: 鉴权并注册成功。
    :status 400: 客户端请求消息格式有误。
    :status 403: 鉴权失败。

    一个客户端通过此路由向服务器发送一个注册请求。

    收到请求后，服务器首先对token进行鉴权，之后验证用户名是否合法，如果验证通过，则返回一个新的token。
    原有的token立即过期，客户端需要使用新的token继续会话。
    """
    try:
        username = request.args["username"]
        passwd = request.args["passwd"]
        token = request.args["token"]
        user = user_manage.jwt_decode(token)
        new_token = user_manage.register(user, username, passwd)
        return jsonify({"token": new_token}), 200
    except jwt.InvalidTokenError:
        abort(403)
    except KeyError:
        abort(400)


if __name__ == '__main__':
    app.run()
