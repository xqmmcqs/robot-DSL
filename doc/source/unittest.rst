单元测试
========

测试脚本
========

对于后端的每个模块（词法分析、动作、条件、状态机、用户状态）都有对应的单元测试，例如，运行 ``parser`` 模块的单元测试：

.. code-block::

    python -m test.test_parser

会得到如下结果：

.. code-block::

    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.014s

    OK

可用的单元测试模块如下：

.. code-block::

    test.test_app
    test.test_parser
    test.test_speak_action
    test.test_update_action
    test.test_state_machine
    test.test_user_state

测试桩
======

为了对客户端进行测试，``stub.py`` 实现了一个具有简单功能的后端，仅有两个状态，并且支持登录和注册操作。

运行测试桩的命令如下：

.. code-block::

    python test/stub.py

压力测试
========

为了测试线程安全和多客户端访问服务器时服务器的承受能力，我设计了压力测试，并行开启100个客户端对服务器发送请求，请求均为对数据库的访问，运行压力测试的命令如下：

.. code-block::

    python -m test.test_pressure