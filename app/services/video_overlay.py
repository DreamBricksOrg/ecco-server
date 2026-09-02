"""Aplica um overlay de imagem fixo sobre um vídeo gravado, via ffmpeg"""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_OVERLAY_IMAGE_PATH = Path(__file__).resolve().parent.parent / "assets" / "ecco_msg.png"


def _find_ffprobe(ffmpeg_path: str) -> Optional[str]:
    """Localiza o ffprobe: primeiro no PATH, senão ao lado do binário do ffmpeg"""
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        return ffprobe_path

    candidate = Path(ffmpeg_path).with_name(Path(ffmpeg_path).name.replace("ffmpeg", "ffprobe"))
    return str(candidate) if candidate.is_file() else None


def _get_video_resolution(ffprobe_path: str, video_path: Path) -> Optional[Tuple[int, int]]:
    """Obtém (largura, altura) do primeiro stream de vídeo, via ffprobe"""
    try:
        result = subprocess.run(
            [
                ffprobe_path,
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                str(video_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f"ffprobe falhou ao ler resolução de {video_path.name}: {result.stderr.strip()}")
            return None

        width_str, height_str = result.stdout.strip().split("x")
        return int(width_str), int(height_str)
    except Exception as e:
        logger.error(f"Erro inesperado ao obter resolução de {video_path.name}: {e}")
        return None


def apply_overlay(video_path: Path) -> bool:
    """Composita app/assets/ecco_msg.png sobre todo o vídeo em video_path, sobrescrevendo-o.

    Reencoda o vídeo com o overlay esticado para preencher exatamente a resolução
    do vídeo de entrada e presente do início ao fim. Em caso de falha (ffmpeg/ffprobe
    ausente, erro de processamento etc.), loga o erro e deixa o arquivo original
    intacto — quem chamar continua servindo o vídeo sem overlay.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        logger.error("ffmpeg não encontrado no PATH; overlay não será aplicado")
        return False

    ffprobe_path = _find_ffprobe(ffmpeg_path)
    if not ffprobe_path:
        logger.error("ffprobe não encontrado; overlay não será aplicado")
        return False

    if not _OVERLAY_IMAGE_PATH.is_file():
        logger.error(f"Imagem de overlay não encontrada: {_OVERLAY_IMAGE_PATH}")
        return False

    if not video_path.is_file():
        logger.error(f"Vídeo não encontrado para aplicar overlay: {video_path}")
        return False

    resolution = _get_video_resolution(ffprobe_path, video_path)
    if not resolution:
        return False
    width, height = resolution

    fd, tmp_name = tempfile.mkstemp(suffix=video_path.suffix, dir=str(video_path.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)

    try:
        result = subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-i", str(video_path),
                "-loop", "1",
                "-i", str(_OVERLAY_IMAGE_PATH),
                "-filter_complex",
                f"[1:v]scale={width}:{height}[ovr];"
                "[0:v][ovr]overlay=0:0:shortest=1:format=auto,format=yuv420p[v]",
                "-map", "[v]",
                "-map", "0:a?",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "20",
                "-c:a", "copy",
                "-movflags", "+faststart",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(
                f"ffmpeg falhou ao aplicar overlay em {video_path.name} "
                f"(código {result.returncode}): {result.stderr.strip()[-2000:]}"
            )
            return False

        os.replace(tmp_path, video_path)
        logger.info(f"Overlay aplicado com sucesso em {video_path.name}")
        return True
    except Exception as e:
        logger.error(f"Erro inesperado ao aplicar overlay em {video_path.name}: {e}")
        return False
    finally:
        tmp_path.unlink(missing_ok=True)
