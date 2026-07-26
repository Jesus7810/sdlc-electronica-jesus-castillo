from pathlib import Path

from semana2.dia5_evaluacion1.alert_manager import (
    AlertManager,
    ConsoleAlertStrategy,
    FileAlertStrategy,
)


class FakeAlertStrategy:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message: str) -> None:
        self.messages.append(message)


def test_alert_manager_delegates_message_to_strategy() -> None:
    strategy = FakeAlertStrategy()
    manager = AlertManager(strategy)

    manager.send_alert("TEMP-01: 38.0 °C")

    assert strategy.messages == ["TEMP-01: 38.0 °C"]


def test_console_strategy_prints_message(capsys: object) -> None:
    strategy = ConsoleAlertStrategy()

    strategy.send("HUM-01: 85.0 %")

    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert captured.out == "HUM-01: 85.0 %\n"


def test_file_strategy_appends_messages(tmp_path: Path) -> None:
    alerts_file = tmp_path / "alerts.txt"
    strategy = FileAlertStrategy(alerts_file)

    strategy.send("TEMP-01: 38.0 °C")
    strategy.send("HUM-01: 85.0 %")

    assert alerts_file.read_text(encoding="utf-8") == (
        "TEMP-01: 38.0 °C\n"
        "HUM-01: 85.0 %\n"
    )