import bnetcli as pkg


def test_main_prints(capsys):
    pkg.main()
    captured = capsys.readouterr()
    assert "Hello from bnetcli!" in captured.out
