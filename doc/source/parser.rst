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

该脚本语言有数个状态定义和变量定义构成。

状态定义包括标识符以及是否需要登录验证，之后 *依次* 包含数个speak动作、数个case子句、一个default子句、数个timeout子句。

变量定义由至少一个变量子句构成。变量子句为变量名、变量类型和默认值。变量名均为"$"开头的、由大小写字母和数字组成的字符串。
变量类型为"Int"、"Real"、"Text"之一。

case子句包含一个条件判断，之后跟随数个update动作或speak动作，再跟随一个可选的goto动作或者exit动作。

default子句包含数个动作，与case子句类似。

timeout子句包含一个整数，之后跟随的动作和case子句类似。

条件判断有长度条件、子串条件、类型条件、串相等条件四种。类型条件可以判断用户输入是否是整数或者浮点数。

speak动作中包含数个由"+"连接的speak内容，在状态定义中直接包含的、以及在timeout子句中包含的speak动作不能出现"Copy"内容，在其他子句中包含的
speak动作可以包含"Copy"，表示以用户输入的字符串替换此处。

update动作包含三个部分：操作、变量名、值。操作可以是"Add"、"Sub"、"Set"之一，值可以是字符串或者数字常量，或者"Copy"。

goto动作表示转移到另一个状态。exit动作表示结束会话。

语法树的形态
------------

解析出的语法树以嵌套列表的形式返回。因此仅有叶节点上存储语法元素，非叶节点均为空。假设根节点在第0层。

第一层表示状态定义或者

API
---

.. autoclass:: server.parser.RobotLanguage
   :members:
