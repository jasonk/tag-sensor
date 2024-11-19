from typer.testing import CliRunner

from tag_sensor.utils import fill_template, fill_templates, parse_color

runner = CliRunner()


def test_parse_colors():
    # NOTE: The tuples are in BGR format, but we accept configurations
    # in RGB.
    assert parse_color("black") == (0, 0, 0)
    assert parse_color("white") == (255, 255, 255)
    assert parse_color("red") == (0, 0, 255)
    assert parse_color("green") == (0, 255, 0)
    assert parse_color("blue") == (255, 0, 0)

    assert parse_color("#000000") == (0, 0, 0)
    assert parse_color("#ffffff") == (255, 255, 255)
    assert parse_color("#FFFFFF") == (255, 255, 255)
    assert parse_color("#ff0000") == (0, 0, 255)
    assert parse_color("#00FF00") == (0, 255, 0)
    assert parse_color("#0000ff") == (255, 0, 0)


def test_fill_template():
    template = "Hello, $name!"
    context = {"name": "world"}
    assert fill_template(template, context) == "Hello, world!"


def test_fill_templates():
    templates = {
        "greetings": ["Hello, $name!", "Goodbye, $name!"],
        "stuff": {"$thing": "This is a $thing"},
        "numbers": [10, 11, 12],
    }
    context = {"name": "world", "thing": "test"}
    assert fill_templates(templates, context) == {
        "greetings": ["Hello, world!", "Goodbye, world!"],
        "stuff": {"test": "This is a test"},
        "numbers": [10, 11, 12],
    }
