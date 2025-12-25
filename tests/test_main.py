from unittest.mock import patch, MagicMock

import pytest

from main import main


@patch("main.handle_open_command")
@patch("main.sys.argv", ["main.py", "open"])
def test_main_open_command(mock_open):
    with patch("main.argparse.ArgumentParser") as mock_parser:
        mock_args = MagicMock()
        mock_args.title = ["open"]
        mock_parser.return_value.parse_args.return_value = mock_args

        main()
        mock_open.assert_called_once()


@patch("main.handle_review_command")
@patch("main.sys.argv", ["main.py", "review"])
def test_main_review_command(mock_review):
    with patch("main.argparse.ArgumentParser") as mock_parser:
        mock_args = MagicMock()
        mock_args.title = ["review"]
        mock_args.select = False
        mock_args.auto_merge = False
        mock_parser.return_value.parse_args.return_value = mock_args

        main()
        mock_review.assert_called_once()


@patch("main.handle_summary_command")
@patch("main.sys.argv", ["main.py", "summary"])
def test_main_summary_command(mock_summary):
    with patch("main.argparse.ArgumentParser") as mock_parser:
        mock_args = MagicMock()
        mock_args.title = ["summary"]
        mock_parser.return_value.parse_args.return_value = mock_args

        main()
        mock_summary.assert_called_once()


@patch("main.handle_summary_ai_command")
@patch("main.sys.argv", ["main.py", "summaryAI"])
def test_main_summary_ai_command(mock_summary_ai):
    with patch("main.argparse.ArgumentParser") as mock_parser:
        mock_args = MagicMock()
        mock_args.title = ["summaryAI"]
        mock_parser.return_value.parse_args.return_value = mock_args

        main()
        mock_summary_ai.assert_called_once()


@patch("main.handle_deploy_command")
@patch("main.sys.argv", ["main.py", "last", "deploy"])
def test_main_deploy_command(mock_deploy):
    with patch("main.argparse.ArgumentParser") as mock_parser:
        mock_args = MagicMock()
        mock_args.title = ["last", "deploy"]
        mock_parser.return_value.parse_args.return_value = mock_args

        main()
        mock_deploy.assert_called_once()


@patch("main.handle_report_command")
@patch("main.sys.argv", ["main.py", "report", "Test", "30"])
def test_main_report_command(mock_report):
    with patch("main.argparse.ArgumentParser") as mock_parser:
        mock_args = MagicMock()
        mock_args.title = ["report", "Test", "30"]
        mock_parser.return_value.parse_args.return_value = mock_args

        main()
        mock_report.assert_called_once_with(["report", "Test", "30"])


@patch("main.sys.argv", ["main.py", "ai", "review"])
def test_main_ai_review_command():
    with patch("main.argparse.ArgumentParser") as mock_parser:
        mock_args = MagicMock()
        mock_args.title = ["ai", "review"]
        mock_parser.return_value.parse_args.return_value = mock_args

        with patch("ai_code_review.run_review") as mock_ai_review:
            main()
            mock_ai_review.assert_called_once()


@patch("main.sys.argv", ["main.py"])
def test_main_no_args_shows_help():
    with patch("main.argparse.ArgumentParser") as mock_parser:
        mock_parser_instance = MagicMock()
        mock_parser.return_value = mock_parser_instance

        with pytest.raises(SystemExit):
            main()

        mock_parser_instance.print_help.assert_called_once()
