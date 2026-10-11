import pytest

from weight_up.xiaomi import XiaomiAuthError, XiaomiAuthResult, cli

AUTH = XiaomiAuthResult("SECRET-SSECURITY-KEY", "SECRET-SERVICE-TOKEN", "7", "c7",
                        "SECRET-PASS-TOKEN")


def run(monkeypatch, capsys, argv, log_in=lambda args: AUTH, verify=lambda *a: None):
    monkeypatch.setattr(cli, "_log_in", log_in)
    monkeypatch.setattr(cli, "verify_tokens", verify)
    code = cli.main(argv)
    return code, capsys.readouterr().out


def test_either_email_or_user_id_is_required():
    with pytest.raises(SystemExit):
        cli._parse_args([])
    with pytest.raises(SystemExit):
        cli._parse_args(["a@b.c", "--user-id", "7"])


def test_success_prints_pass_and_never_the_full_secrets(monkeypatch, capsys):
    code, output = run(monkeypatch, capsys, ["a@b.c", "-r", "sg"])

    assert code == 0
    assert "verification:  PASS - sg.api.io.mi.com" in output
    for secret in ("SECRET-SSECURITY-KEY", "SECRET-SERVICE-TOKEN", "SECRET-PASS-TOKEN"):
        assert secret not in output


def test_pass_token_is_printed_in_full_only_on_request(monkeypatch, capsys):
    _, output = run(monkeypatch, capsys, ["a@b.c", "--show-pass-token"])

    assert "SECRET-PASS-TOKEN" in output
    assert "SECRET-SSECURITY-KEY" not in output


def test_a_failed_login_prints_the_reason_and_exits_non_zero(monkeypatch, capsys):
    def failing(args):
        raise XiaomiAuthError("passToken rejected (result=error)")

    code, output = run(monkeypatch, capsys, ["a@b.c"], log_in=failing)

    assert code == 1
    assert "FAIL - passToken rejected" in output


def test_missing_pass_token_is_shown_as_missing():
    assert cli._mask(None) == "<missing>"
    assert cli._mask("abcdefgh") == "abcd... (8 chars)"


def test_captcha_folder_is_created_on_demand(tmp_path, monkeypatch):
    captcha_dir = tmp_path / "captcha"
    monkeypatch.setattr(cli, "CAPTCHA_DIR", captcha_dir)
    monkeypatch.setattr("builtins.input", lambda prompt="": "text")

    assert not captcha_dir.exists()
    assert cli._prompt_captcha(b"IMAGE") == "text"

    [saved] = captcha_dir.iterdir()
    assert saved.read_bytes() == b"IMAGE"


def test_captcha_folder_sits_next_to_auth_py():
    assert cli.CAPTCHA_DIR == cli.Path(cli.__file__).parent / "captcha"
