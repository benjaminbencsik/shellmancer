from shellmancer.protocol import parse_action


def test_parse_shell_json():
    action = parse_action('{"type":"shell","command":"pwd"}')
    assert action.type == "shell"
    assert action.command == "pwd"


def test_parse_fenced_json():
    action = parse_action('```json\n{"type":"final","message":"done"}\n```')
    assert action.type == "final"
    assert action.message == "done"


def test_plain_text_recovers_as_final():
    action = parse_action("hello")
    assert action.type == "final"
    assert action.message == "hello"
