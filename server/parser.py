import pyparsing as pp


class RobotLanguage:
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
            _string_constant("string") ^ pp.Keyword("Copy")))))
    _speak_content = _variable ^ _string_constant
    _speak_action = pp.Group(pp.Keyword("Speak") + pp.Group(
        (_speak_content + pp.ZeroOrMore('+' + _speak_content)).set_parse_action(lambda tokens: tokens[0::2])))
    _speak_action_copy = pp.Group(pp.Keyword("Speak") + pp.Group(((_speak_content ^ pp.Keyword("Copy")) + pp.ZeroOrMore(
        '+' + (_speak_content ^ pp.Keyword("Copy")))).set_parse_action(lambda tokens: tokens[0::2])))
    _actions = _exit_action ^ _goto_action ^ _update_action ^ _speak_action_copy

    _case_clause = pp.Group(
        pp.Keyword("Case") + _conditions + pp.Group(pp.ZeroOrMore(_update_action ^ _speak_action_copy) + pp.Opt(
            _exit_action ^ _goto_action)))
    _default_clause = pp.Group(
        pp.Keyword("Default") + pp.Group(pp.ZeroOrMore(_update_action ^ _speak_action_copy) + pp.Opt(
            _exit_action ^ _goto_action)))
    _timeout_clause = pp.Group(
        pp.Keyword("Timeout") + _integer_constant + pp.Group(pp.ZeroOrMore(_speak_action) + pp.Opt(
            _exit_action ^ _goto_action)))

    _state_definition = pp.Group(
        pp.Keyword("State") + pp.Word(pp.alphas) + pp.Group(pp.Opt(pp.Keyword("Verified"))) + pp.Group(
            pp.ZeroOrMore(_speak_action)) + pp.Group(pp.ZeroOrMore(_case_clause)) + _default_clause + pp.Group(
            pp.ZeroOrMore(_timeout_clause)))
    _language = pp.ZeroOrMore(_state_definition ^ _variable_definition)

    @staticmethod
    def parse_files(files: list[str]) -> list[pp.ParseResults]:
        result = []
        for file in files:
            if len(file) == 0:
                continue
            result += RobotLanguage._language.parse_file(file, parse_all=True).as_list()
        return result


if __name__ == '__main__':
    print(RobotLanguage.parse_files(["grammar.txt"]))
