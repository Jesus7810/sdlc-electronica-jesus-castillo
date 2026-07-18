import json


class DataRecorder:
    """Guarda información en formato JSON Lines."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def record(self, data: dict) -> None:
        with open(self.file_path, "a", encoding="utf-8") as file:
            file.write(json.dumps(data) + "\n")