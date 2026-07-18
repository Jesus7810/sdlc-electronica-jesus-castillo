from uart_driver.recorder import DataRecorder
import json

def test_recorder_creates_file(tmp_path) -> None:
    """Debe crear el archivo al guardar datos."""
    file_path = tmp_path / "data.jsonl"
    recorder = DataRecorder(str(file_path))
    recorder.record({"value": 10})
    assert file_path.exists()


def test_recorder_writes_json(tmp_path) -> None:
    """Debe escribir un objeto JSON válido."""
    file_path = tmp_path / "data.jsonl"
    recorder = DataRecorder(str(file_path))
    recorder.record({"value": 10})
    content = file_path.read_text(encoding="utf-8")
    saved_data = json.loads(content)
    assert saved_data["value"] == 10


def test_recorder_writes_multiple_lines(tmp_path) -> None:
    """Debe guardar cada registro en una línea."""
    file_path = tmp_path / "data.jsonl"
    recorder = DataRecorder(str(file_path))
    recorder.record({"value": 10})
    recorder.record({"value": 20})
    lines = file_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2