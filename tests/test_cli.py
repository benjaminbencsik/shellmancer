from shellmancer.cli import build_parser


def test_thinking_is_disabled_by_default() -> None:
    args = build_parser().parse_args(["inspect"])
    assert args.think is False


def test_think_flag_enables_thinking() -> None:
    args = build_parser().parse_args(["--think", "review"])
    assert args.think is True


def test_yolo_flag_enables_yolo_mode() -> None:
    args = build_parser().parse_args(["--yolo", "run"])
    assert args.yolo is True
    assert args.no_yolo_warning is False


def test_yes_alias_enables_yolo_mode() -> None:
    args = build_parser().parse_args(["--yes", "run"])
    assert args.yolo is True


def test_short_y_alias_enables_yolo_mode() -> None:
    args = build_parser().parse_args(["-y", "run"])
    assert args.yolo is True


def test_yolo_warning_can_be_suppressed() -> None:
    args = build_parser().parse_args(["--yolo", "--no-yolo-warning", "run"])
    assert args.yolo is True
    assert args.no_yolo_warning is True


def test_display_is_polished_by_default() -> None:
    args = build_parser().parse_args(["inspect"])
    assert args.verbose is False
    assert args.quiet is False
    assert args.no_color is False
    assert args.no_animation is False


def test_verbose_mode_can_be_enabled() -> None:
    args = build_parser().parse_args(["--verbose", "inspect"])
    assert args.verbose is True


def test_terminal_effects_can_be_disabled() -> None:
    args = build_parser().parse_args(["--no-color", "--no-animation", "inspect"])
    assert args.no_color is True
    assert args.no_animation is True
