# robot-DSL

一个应用于在线机器人的脚本语言及其解释器，配有相应客户端。

## 特性

- 基于状态机的应答逻辑。
- 用户注册/登录，`JWT` 鉴权。
- 自定义用户变量，持久化访问。
- 基于 [PyParsing](https://pyparsing-docs.readthedocs.io/en/latest/index.html) 的解释器。
- PyQt5 & QtQuick 实现的客户端。

## 用户指南

`config.json`配置文件条目解释：

- `key`: JWT密钥；
- `db_path`：数据库文件路径，相对于主目录；
- `source`：脚本文件路径的列表，相对于主目录。

安装依赖：

```
pip install -r requirements.txt
```

启动服务端：

```
python -m flask run
```

启动客户端：

```
cd client
python main.py
```
