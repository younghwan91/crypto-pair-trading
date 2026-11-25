"""Smoke test: the README offline demo must keep running on synthetic data."""

from quantbox.examples.offline_demo import main


def test_offline_demo_runs(capsys):
    main()
    out = capsys.readouterr().out
    assert "AAAUSDT/BBBUSDT: passed=True" in out
    assert "Backtest (synthetic data" in out
