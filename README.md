# 一种领域特定脚本语言的解释器的设计与实现

学号：2019211397

姓名：毛子恒

## 文档

推荐内容和doc.pdf相同但是观感更好的[在线文档](https://xqmmcqs.com/DSL/index.html)

## 用户指南

`config.json`配置文件条目解释：

- `key`: JWT密钥；
- `db_path`：数据库文件路径，相对于主目录。
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
