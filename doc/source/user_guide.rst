用户指南
========

安装依赖：

.. code-block::

    pip install -r requirements.txt

``config.json`` 配置文件条目解释：

- ``key``: JWT密钥；
- ``db_path``：数据库文件路径，相对于主目录；
- ``source``：脚本文件路径的列表，相对于主目录。

启动服务端：

.. code-block::

    python -m flask run

启动客户端：

.. code-block::

    cd client
    python main.py
