"""Relógio em tela cheia para testar gravações do OBS.

Uso: python tools/fullscreen_clock.py [--monitor N]
Sem --monitor, usa o último monitor detectado (geralmente o secundário).
Sair: ESC ou fechar a janela.
"""

import argparse
import os
import sys
from datetime import datetime

# Evita que a janela minimize ao perder o foco (ex: clicar em outro monitor).
# Precisa ser definido antes do pygame.init() para a hint do SDL surtir efeito.
os.environ["SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS"] = "0"

import pygame

BACKGROUND_COLOR = (10, 10, 10)
TEXT_COLOR = (0, 255, 120)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Relógio em tela cheia para teste de gravação OBS")
    parser.add_argument(
        "--monitor",
        type=int,
        default=None,
        help="Índice do monitor (0 = principal). Padrão: último monitor detectado.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    pygame.init()
    pygame.display.set_caption("Relógio - Teste de Gravação OBS")

    num_displays = pygame.display.get_num_displays()
    monitor = args.monitor if args.monitor is not None else num_displays - 1
    monitor = max(0, min(monitor, num_displays - 1))

    print(f"Monitores detectados: {num_displays} | usando o monitor {monitor}")

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, display=monitor)
    width, height = screen.get_size()

    font_size = height // 6
    font = pygame.font.SysFont("consolas,couriernew,monospace", font_size, bold=True)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        now = datetime.now()
        text = now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"

        screen.fill(BACKGROUND_COLOR)
        surface = font.render(text, True, TEXT_COLOR)
        rect = surface.get_rect(center=(width // 2, height // 2))
        screen.blit(surface, rect)
        pygame.display.flip()

        clock.tick(0)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
