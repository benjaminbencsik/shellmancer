from shellmancer.cli import build_parser


def test_thinking_is_disabled_by_default() -> None:
    args = build_parser().parse_args(["hello"])
    assert args.think is False


def test_think_flag_enables_thinking() -> None:
    args = build_parser().parse_args(["--think", "solve", "this"])
    assert args.think is True


def test_yolo_flag_enables_yolo_mode() -> None:
    args = build_parser().parse_args(["--yolo", "do", "something"])
    assert args.yolo is True
    assert args.no_yolo_warning is False


def test_yes_alias_enables_yolo_mode() -> None:
    args = build_parser().parse_args(["--yes", "do", "something"])
    assert args.yolo is True


def test_short_y_alias_enables_yolo_mode() -> None:
    args = build_parser().parse_args(["-y", "do", "something"])
    assert args.yolo is True


def test_yolo_warning_can_be_suppressed() -> None:
    args = build_parser().parse_args(
        ["--yolo", "--no-yolo-warning", "do", "something"]
    )
    assert args.yolo is True
    assert args.no_yolo_warning is True
