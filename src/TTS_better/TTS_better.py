import subprocess
from pathlib import Path
import time
import uuid
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TTS_better:
    """TTS usando Piper via Docker - modo bloqueante"""
    container_name: str = "tts"
    output_dir: str = "tmp"
    length_scale: float = 1.0
    noise_scale: float = 0.5
    noise_w: float = 0.7

    def __post_init__(self):
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.piper_bin = "/data/piper/piper"
        self.model_path = "/data/piper/models/pt_BR-faber-medium/pt_BR-faber-medium.onnx"

    def generate(self, text: str, filename: str = None) -> Path:
        """Geração bloqueante de TTS"""
        if filename is None:
            filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
        output_path = self.output_dir / filename

        cmd = [
            "docker", "exec", "-i",
            "-e", "LANG=C.UTF-8",
            self.container_name,
            self.piper_bin,
            "--model", self.model_path,
            "--length_scale", str(self.length_scale),
            "--noise_scale", str(self.noise_scale),
            "--noise_w", str(self.noise_w),
            "--output_file", f"/data/tmp/{filename}",
        ]

        result = subprocess.run(
            cmd,
            input=text.encode('utf-8'),
            capture_output=True,
            timeout=30
        )

        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='replace')
            raise RuntimeError(f"Piper TTS falhou: {stderr}")

        if not output_path.exists():
            raise FileNotFoundError(f"Arquivo {output_path} não foi criado")

        logger.info(f"TTS gerado: {output_path}")
        return output_path

    def play(self, filename: str):
        """Reproduz um WAV bloqueante"""
        path = self.output_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"{path} não existe. Gere-o primeiro.")
        subprocess.run(["aplay", str(path)], check=True)
        logger.info(f"Reprodução concluída: {filename}")

    def cleanup_old_wavs(self, max_age_seconds: int = 60, exclude: str = None):
        """Remove arquivos WAV antigos"""
        now = time.time()
        removed = 0
        for wav in self.output_dir.glob("*.wav"):
            if exclude and wav.name == exclude:
                continue
            try:
                if now - wav.stat().st_mtime > max_age_seconds:
                    wav.unlink()
                    removed += 1
            except (FileNotFoundError, PermissionError):
                pass
        if removed > 0:
            logger.info(f"Limpeza: {removed} arquivo(s) removido(s)")

# ===== Exemplos de uso =====
# if __name__ == "__main__":
#     tts = PiperTTS(length_scale=1.3, noise_scale=0.2, noise_w=0.05)
    
#     # Gerar e tocar bloqueante
#     wav_file = tts.generate("Olá mundo, esta é uma voz mais grossa e lenta.", "teste.wav")
#     tts.play("teste.wav")
    
#     # Limpeza de arquivos antigos
#     tts.cleanup_old_wavs(max_age_seconds=30)
