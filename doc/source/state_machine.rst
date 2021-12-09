客服机器人逻辑
==============

概述
----

客服机器人与用户的交互一般为一问一答或者一问多答，因此客服机器人的底层逻辑被设计为一个拓广的Mealy状态机，其输入可能是用户字符串，或者用户未执行操作的秒数；其输出通常是一个字符串序列。

针对用户的输入，机器人可以对各个可行的转移 *条件* 进行判断，如果满足某个条件，则执行该分支下的所有 *动作* 。

此外，可以自定义一些用户变量，用于简单存储相关的信息，用户变量持久保存在数据库中。

用户变量
--------

在客服机器人中，可以自定义整型、浮点数型和字符串型的用户变量，用户变量名是以 ``$`` 开头的字母/数字串。顾名思义，用户变量值是每个用户独有的，但是每个用户都拥有相同种类和数量的用户变量。每个用户变量有一个默认值，在注册新用户时自动赋予，在脚本中可以使用 ``Update`` 动作触发用户变量的修改，也可以使用 ``Speak`` 动作向用户输出用户变量的值。

开始一个新会话时，用户默认分配到一个访客账户，用户之后可以注册或者登录自己的账户，由于访客账户是所有用户共有的，所以不能更改属于访客账户的变量。更多信息请参考 :ref:`verified-label`。

用户变量保存在SQLite数据库中，通过Storm库进行ORM访问。在分析脚本语言的过程中，会根据脚本中对于用户变量的定义建立数据库，每个用户关联到数据库中的一行，每个属性为数据库中的一列。

Storm库不是线程安全的，因此每次数据库访问都需要互斥锁。

转移逻辑
--------

如前所述，对于输入是用户字符串的情况，状态机中的每个状态会保存一个转移条件 *列表* ，状态机依次检查列表中的每一个条件，如果用户的输入满足一个条件，则执行该条件下的所有动作，并且忽略之后的所有条件。每个状态必须有一个 ``Default`` 转移，表示当条件列表中的条件都不满足时，执行默认的动作。简而言之，条件的检查类似于 ``if-elif-else`` 逻辑。

对于输入是用户未执行操作的秒数，状态机中的每个状态会保存一个超时转移 *字典* ，客户端应当每隔一段时间返回用户未操作的秒数，状态机检查字典中是否包含当前时间间隔中的时刻，如果包含，就执行相应的动作。

转移条件
--------

对于用户输入的字符串，可以执行以下几种条件判断：

* 判断其输入长度是否满足限制，参考 :py:class:`server.state_machine.LengthCondition`。
* 判断其输入是否包含某个字符串，参考 :py:class:`server.state_machine.ContainCondition`。
* 判断其输入字面值是否是某种类型，参考 :py:class:`server.state_machine.TypeCondition`。
* 判断其输入是否和某个串相同，参考 :py:class:`server.state_machine.EqualCondition`。

.. _action:

动作
----

.. _verified-label:

Update动作
^^^^^^^^^^

更新一个用户变量，更新的操作有以下三种：

* ``Add``，适用于整型或浮点型的变量。
* ``Sub``，适用于整型或浮点型的变量。
* ``Set``，适用于任何变量。

更新的值有两种：

* 字符串或数字字面值。
* Copy，表示用户的输入。

编译器会检查字面值和用户变量的类型是否匹配，由于无法直接检查用户的输入，因此当更新的值为Copy时，Update动作需要包括在判断用户输入类型的子句中，保证用户输入和用户变量的类型兼容。

为了保证不能更新访客用户的属性，或者避免用户访问到访客用户的某些变量，在定义状态时可选指定 ``Verified`` ，标识该状态需要登录才可以进入，访客用户进入该状态的请求会被拒绝。Update子句只能定义在指定了 ``Verified`` 的状态中。

参考 :py:class:`server.state_machine.UpdateAction`。

Speak动作
^^^^^^^^^

向用户返回一个字符串，字符串可以由多个部分组成，各个部分之间用 ``+`` 连接。每个部分可以是以下三种之一：

* 由半角双引号包括的字符串常量。
* 变量名。
* Copy，表示用户的输入。

参考 :py:class:`server.state_machine.SpeakAction`。

Exit动作
^^^^^^^^

结束一个会话，简单地将用户的状态设为-1表示会话结束。

参考 :py:class:`server.state_machine.ExitAction`。

Goto动作
^^^^^^^^

转移到另一个状态。

参考 :py:class:`server.state_machine.GotoAction`。

状态机
------

:py:class:`server.state_machine.StateMachine` 是对上述状态机的实现。

构建状态机时，首先调用语法分析模块，在返回的分析树的基础上进行语义分析，并且构建模型。

状态机提供条件转移和超时转移两个接口，可以根据给定的用户状态和用户输入进行状态转移，并且返回需要输出给用户的字符串列表。

API
---

.. autoclass:: server.state_machine.UserVariableSet
   :members:
.. autoclass:: server.state_machine.Condition
   :members:
.. autoclass:: server.state_machine.LengthCondition
   :members:
.. autoclass:: server.state_machine.ContainCondition
   :members:
.. autoclass:: server.state_machine.TypeCondition
   :members:
.. autoclass:: server.state_machine.EqualCondition
   :members:
.. autoclass:: server.state_machine.Action
   :members:
.. autoclass:: server.state_machine.ExitAction
   :members:
.. autoclass:: server.state_machine.GotoAction
   :members:
.. autoclass:: server.state_machine.UpdateAction
   :members:
.. autoclass:: server.state_machine.SpeakAction
   :members:
.. autoclass:: server.state_machine.CaseClause
   :members:
.. autoclass:: server.state_machine.StateMachine
   :members:
   :private-members:

异常
----

.. autoclass:: server.state_machine.LoginError
   :members:
.. autoclass:: server.state_machine.GrammarError
   :members:
