import subprocess
from pathlib import Path
import time

class TTS:
    def __init__(
        self,
        container_name: str = "tts",
        output_dir: str = "src/TTS/tmp",
        voice: str = "mb/mb-br3",
        speed: int = 120,
        pitch: int = 38,
        gap: int = 6,
        amplitude: int = 110,
    ):
        self.container = container_name
        self.voice = voice
        self.speed = speed
        self.pitch = pitch
        self.gap = gap
        self.amplitude = amplitude

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def cleanup_old_wavs(
        self,
        max_age_seconds: int = 60,
        exclude: str | None = None
        ) -> None:
        now = time.time()

        for wav in self.output_dir.glob("*.wav"):
            if exclude and wav.name == exclude:
                continue

            try:
                if now - wav.stat().st_mtime > max_age_seconds:
                    wav.unlink()
            except FileNotFoundError:
                pass



    def generate(self, text: str, filename: str = "speech.wav") -> Path:
        self.cleanup_old_wavs(exclude=filename)
        output_path = self.output_dir / filename

        cmd = [
            "docker", "exec", "-i",
            "-e", "LANG=C.UTF-8",
            self.container,
            "espeak-ng",
            "-v", self.voice,
            "-s", str(self.speed),
            "-p", str(self.pitch),
            "-g", str(self.gap),
            "-a", str(self.amplitude),
            "-w", f"/data/{filename}",
            text,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"TTS failed:\nSTDERR:\n{result.stderr}"
            )

        return output_path
    
    def play(self, filename: str = "speech.wav"):
        subprocess.run(["aplay", filename])