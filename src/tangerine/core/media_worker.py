import subprocess
from pathlib import Path


class MediaWorker:
    @staticmethod
    def convert(src: Path, dst: Path) -> Path:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), str(dst)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return dst

    @staticmethod
    def compress_media(src: Path, dst: Path) -> Path:
        # Compresses video using H.264 CRF 28 or audio at 128k
        if src.suffix.lower() in {".mp3", ".wav", ".flac", ".ogg", ".m4a"}:
            cmd = ["ffmpeg", "-y", "-i", str(src), "-b:a", "128k", str(dst)]
        else:
            cmd = ["ffmpeg", "-y", "-i", str(src), "-vcodec", "libx264", "-crf", "28", "-preset", "fast", str(dst)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return dst

    @staticmethod
    def trim_media(src: Path, dst: Path, start_sec: str = "00:00:00", duration_sec: str = "00:00:15") -> Path:
        cmd = [
            "ffmpeg", "-y", "-ss", start_sec, "-i", str(src),
            "-t", duration_sec, "-c", "copy", str(dst)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return dst

    @staticmethod
    def extract_audio(src: Path, dst: Path) -> Path:
        cmd = ["ffmpeg", "-y", "-i", str(src), "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(dst)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return dst