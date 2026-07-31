from unittest.mock import MagicMock, patch

from app.templates import render


class TestRender:
    def test_render_calls_jinja(self):
        with patch("app.templates._jinja_env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "<html></html>"
            mock_env.get_template.return_value = mock_template

            result = render("test.html", title="Hello")

            mock_env.get_template.assert_called_once_with("test.html")
            mock_template.render.assert_called_once_with(title="Hello")
            assert result == "<html></html>"

    def test_render_no_context(self):
        with patch("app.templates._jinja_env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = ""
            mock_env.get_template.return_value = mock_template

            result = render("empty.html")

            mock_template.render.assert_called_once_with()
            assert result == ""
