"""Templates Jinja2 compartidos entre todos los modulos."""

import pathlib

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = str(pathlib.Path(__file__).parent.parent / "templates")

_jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)


def render(name: str, **context: object) -> str:
    template = _jinja_env.get_template(name)
    return template.render(**context)
