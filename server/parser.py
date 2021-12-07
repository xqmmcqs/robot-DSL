"""词法、语法分析模块。

此模块从文件中读取脚本文件，利用预先定义的领域特定脚本语言文法进行词法分析和语法分析，并且返回一个语法树。

该脚本语言语法的BNF定义如下：

.. code-block::

    <language>            ::= {<state_definition> | <variable_definition>}
    <state_definition>    ::= "State" <identifier> ["Verified"] {<speak_action>} {<case_clause>} <default_clause> {<timeout_clause>}
    <identifier>          ::= <letter>+
    <letter>              ::= "A" | "B" | ... "Z" | "a" | "b" | ... | "z"
    <speak_action>        ::= "Speak" <speak_content> {"+" <speak_content>}
    <speak_content>       ::= <variable> | <string_constant>
    <variable>            ::= "$" (<letter> | "_") {<letter> | <number> | "_"}
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

变量定义由至少一个变量子句构成。

case子句包含一个条件判断，之后跟随数个update动作或speak动作，再跟随一个可选的goto动作或者exit动作。

default子句包含数个动作，与case子句类似。

timeout子句包含一个整数，之后跟随的动作和case子句类似。

条件判断有长度条件、子串条件、类型条件、串相等条件四种。类型条件可以判断用户输入是否是整数或者浮点数。

speak动作中包含数个由"+"连接的speak内容，在状态定义中直接包含的、以及在timeout子句中包含的speak动作不能出现"Copy"内容，在其他子句中包含的
speak动作可以包含"Copy"，表示以用户输入的字符串替换此处。

update动作表示对
"""

import pyparsing as pp


class RobotLanguage(object):
    """脚本语言对象。

    定义脚本语言的文法，以及对一个文件列表进行分析的方法。
    """
    _integer_constant = pp.Regex("[-+]?[0-9]+").set_parse_action(lambda tokens: int(tokens[0]))
    _real_constant = pp.Regex("[-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?").set_parse_action(
        lambda tokens: float(tokens[0]))
    _string_constant = pp.quoted_string('"')

    _variable = pp.Combine('$' + pp.Regex("[A-Za-z_][0-9A-Za-z_]*"))
    _variable_clause = pp.Group(_variable + (
            (pp.Keyword("Int") + _integer_constant) ^ (pp.Keyword("Real") + _real_constant) ^ (
            pp.Keyword("Text") + _string_constant)))
    _variable_definition = pp.Group(pp.Keyword("Variable") + pp.Group(pp.OneOrMore(_variable_clause)))

    _length_condition = pp.Keyword("Length") + pp.oneOf("< > <= >= =") + _integer_constant
    _contain_condition = pp.Keyword("Contain") + _string_constant
    _type_condition = pp.Keyword("Type") + (pp.Keyword("Int") ^ pp.Keyword("Real"))
    _equal_condition = _string_constant
    _conditions = _length_condition ^ _contain_condition ^ _type_condition ^ _equal_condition

    _exit_action = pp.Group(pp.Keyword("Exit"))
    _goto_action = pp.Group(pp.Keyword("Goto") + pp.Word(pp.alphas))
    _update_action = pp.Group(pp.Keyword("Update") + _variable + (((pp.Keyword("Add") ^ pp.Keyword("Sub") ^ pp.Keyword(
        "Set")) + (_real_constant ^ pp.Keyword("Copy"))) ^ (pp.Keyword("Set") + (
                _string_constant ^ pp.Keyword("Copy")))))
    _speak_content = _variable ^ _string_constant
    _speak_action = pp.Group(pp.Keyword("Speak") + pp.Group(
        (_speak_content + pp.ZeroOrMore('+' + _speak_content)).set_parse_action(lambda tokens: tokens[0::2])))
    _speak_action_copy = pp.Group(pp.Keyword("Speak") + pp.Group(((_speak_content ^ pp.Keyword("Copy")) + pp.ZeroOrMore(
        '+' + (_speak_content ^ pp.Keyword("Copy")))).set_parse_action(lambda tokens: tokens[0::2])))

    _case_clause = pp.Group(
        pp.Keyword("Case") + _conditions + pp.Group(pp.ZeroOrMore(_update_action ^ _speak_action_copy) + pp.Opt(
            _exit_action ^ _goto_action)))
    _default_clause = pp.Group(
        pp.Keyword("Default") + pp.Group(pp.ZeroOrMore(_update_action ^ _speak_action_copy) + pp.Opt(
            _exit_action ^ _goto_action)))
    _timeout_clause = pp.Group(
        pp.Keyword("Timeout") + _integer_constant + pp.Group(pp.ZeroOrMore(_update_action ^ _speak_action) + pp.Opt(
            _exit_action ^ _goto_action)))

    _state_definition = pp.Group(
        pp.Keyword("State") + pp.Word(pp.alphas) + pp.Group(pp.Opt(pp.Keyword("Verified"))) + pp.Group(
            pp.ZeroOrMore(_speak_action)) + pp.Group(pp.ZeroOrMore(_case_clause)) + _default_clause + pp.Group(
            pp.ZeroOrMore(_timeout_clause)))
    _language = pp.ZeroOrMore(_state_definition ^ _variable_definition)

    @staticmethod
    def parse_files(files: list[str]) -> list[pp.ParseResults]:
        """解析一个脚本，脚本存储在一系列文件中。

        :param files: 文件名列表。
        :return: 解析脚本得到的语法树。
        """
        result = []
        for file in files:
            if len(file) == 0:
                continue
            result += RobotLanguage._language.parse_file(file, parse_all=True).as_list()
        return result


if __name__ == '__main__':
    try:
        print(RobotLanguage.parse_files(["../test/parser/case2.txt"]))
    except pp.ParseException as err:
        print(err.explain())
