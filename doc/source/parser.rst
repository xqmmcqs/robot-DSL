脚本语言语法
============

脚本语言语法的定义
------------------

该脚本语言语法的BNF定义如下：

.. code-block::

    <language>            ::= {<state_definition> | <variable_definition>}
    <state_definition>    ::= "State" <identifier> ["Verified"] {<speak_action>} {<case_clause>} <default_clause> {<timeout_clause>}
    <identifier>          ::= <letter>+
    <letter>              ::= "A" | "B" | ... "Z" | "a" | "b" | ... | "z"
    <speak_action>        ::= "Speak" <speak_content> {"+" <speak_content>}
    <speak_content>       ::= <variable> | <string_constant>
    <variable>            ::= "$" (<letter> | <number> | "_")+
    <number>              ::= "0" | "1" | ... | "9"
    <string_constant>     ::= double_quote {character} double_quote
    <case_clause>         ::= "Case" <conditions> {<update_action> | <speak_action_copy>} [<exit_action> <goto_action>]
    <conditions>          ::= <length_condition> | <contain_condition> | <type_condition> | <equal_condition>
    <length_condition>    ::= "Length" ("<" | ">" | "<=" | ">=" | "=") <integer_constant>
    <integer_constant>    ::= {"-" | "+"} <number>+
    <contain_condition>   ::= "Contain" <string_constant>
    <type_condition>      ::= "Type" ("Int" | "Real")
    <equal_condition>     ::= <string_constant>
    <update_action>       ::= "Update" <variable> (<update_real> | <update_string>)
    <update_real>         ::= ("Add" | "Sub" | "Set") (<real_constant> | "Copy")
    <update_string>       ::= "Set" (<string_constant> | "Copy")
    <real_constant>       ::= {"-" | "+"} {<number>} {"."} <number>+ {("e" | "E") {"-" | "+"} <number>+}
    <speak_action_copy>   ::= "Speak" (<speak_content> | "Copy") {"+" (<speak_content> | "Copy")}
    <exit_action>         ::= "Exit"
    <goto_action>         ::= "Goto" <identifier>
    <default_clause>      ::= "Default" {<update_action> | <speak_action_copy>} [<exit_action> <goto_action>]
    <timeout_clause>      ::= "Timeout" <integer_constant> {<update_action> | <speak_action>} [<exit_action> <goto_action>]
    <variable_definition> ::= "Variable" <variable_clause>+
    <variable_clause>     ::= <variable> ("Int" <integer_constant> | "Real" <real_constant> | "Text" <string_constant>)

注：除了 ``<variable>``、``<string_constant>``、``<real_constant>``、``<integer_constant>`` 以外，所有产生式右部的各个属性之间应该以至少一个空白字符分隔，为了增加可读性，定义中略去。

语法规则说明及示例
------------------

本节对脚本语言的语法规则进行简单说明，所有的语法细节无法完全顾及，可以参考上一节的BNF定义。

该脚本语言有数个状态定义和变量定义构成。

变量定义
^^^^^^^^

变量定义由至少一个变量子句构成。变量子句为变量名、变量类型和默认值。变量名均为"$"开头的、由大小写字母和数字组成的字符串。变量类型为 ``Int``、``Real``、``Text`` 之一。默认值必须和变量类型匹配。

一个变量定义的示例如下：

.. code-block::

    Variable
        $trans Int 0
        $billing Real 0
        $name Text "用户"

状态定义
^^^^^^^^

状态定义包括标识符以及一个可选的需要登录验证的标识，之后 *依次* 包含数个Speak动作、数个Case子句、一个Default子句、数个Timeout子句。

一个状态定义的示例如下：

.. code-block::

    State Rename Verified
        Speak "请输入您的新名字，不超过30个字符"
        Case "返回"
            Goto Welcome
        Case Length <= 30
            Speak "您的新名字为" + Copy
            Update $name Set Copy
            Goto Welcome
        Default
            Speak "输入过长"
        Timeout 60
            Speak "您已经很久没有操作了，即将返回主菜单"
            Goto Welcome

Case子句包含一个条件判断，之后跟随数个Update动作或Speak动作，再跟随一个可选的Goto动作或者Exit动作。

Default子句包含数个动作，与Case子句类似。

Timeout子句包含一个整数，之后跟随的动作和Case子句类似。

条件判断
^^^^^^^^

条件判断有长度条件、子串条件、类型条件、串相等条件四种，几种条件判断语句的示例如下：

.. code-block::

    Case Length < 20
    Case Length > 10
    Case Length = 5
    Case Length >= 0
    Case Length <= 200
    Case Contain "hi"
    Case Type Int
    Case Type Real
    Case "no"

动作
^^^^

Speak动作中包含数个由 ``+`` 连接的Speak内容，在状态定义中直接包含的、以及在Timeout子句中包含的Speak动作不能出现 ``Copy`` 内容，在其他子句中包含的Speak动作可以包含 ``Copy`` ，表示以用户输入的字符串替换此处。

Update动作包含三个部分：操作、变量名、值。操作可以是 ``Add``、``Sub``、``Set`` 之一，值可以是字符串或者数字常量，或者 ``Copy``，几个示例如下：

.. code-block::

    Update $billing Sub -1
    Update $name Set Copy

Goto动作后跟随一个状态名称。Exit动作没有参数。

更多语法规则
^^^^^^^^^^^^

即使严格遵循上述语法规则也不能保证写出一个正确的脚本，在语法的定义中无法包含变量名和状态名冲突、Update的变量和值匹配等问题，因此仍然需要参考 :ref:`action` 章节的说明编写脚本。

语法树的形态
------------

:py:class:`server.parser.RobotLanguage` 类内置了上述语法规则，可以实现从文件中读入脚本并且解析，解析出的语法树以嵌套列表的形式返回。因此仅有叶节点上存储语法元素，非叶节点均为空。假设根节点在第0层。

例如，对于以下脚本：

.. code-block::

    Variable
        $name Text "用户"

    State Welcome
        Speak $name + "你好"
        Speak "请输入 退出 以退出"
        Case "退出"
            Exit
        Default
        Timeout 30
            Speak "您已经很久没有操作了，即将于30秒后退出"
        Timeout 60
            Exit

解析得到的文本如下：

.. code-block::

    [['Variable', [['$name', 'Text', '"用户"']]], ['State', 'Welcome', [], [['Speak', ['$name', '"你好"']], ['Speak', ['"请输入 退出 以退出"']]], [['Case', '"退出"', [['Exit']]]], ['Default', []], [['Timeout', 30, [['Speak', ['"您已经很久没有操作了，即将于30秒后退出"']]]], ['Timeout', 60, [['Exit']]]]]]

生成的语法树形态如下图所示：

.. image:: images/tree.*

注：此图中各边上的文字仅用作说明子树的含义，在实际语法树中不出现。

API
---

.. autoclass:: server.parser.RobotLanguage
   :members:
