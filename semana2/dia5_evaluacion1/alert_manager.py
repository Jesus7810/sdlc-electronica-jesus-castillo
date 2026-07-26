from pathlib import Path
from typing import Protocol


class AlertStrategy(Protocol):
    def send(self, message: str) -> None: ...


class AlertManager:
    def __init__(self, strategy: AlertStrategy) -> None:
        self._strategy = strategy

    def send_alert(self, message: str) -> None:
        self._strategy.send(message)


class ConsoleAlertStrategy:
    def send(self, message: str) -> None:
        print(message)


class FileAlertStrategy:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def send(self, message: str) -> None:
        with self._file_path.open(mode="a", encoding="utf-8") as file:
            file.write(f"{message}\n")