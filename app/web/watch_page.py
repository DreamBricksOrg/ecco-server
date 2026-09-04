"""Página HTML de visualização/download do vídeo gravado (servida em /watch/{filename})"""

import base64
from html import escape
from pathlib import Path

_LOGO_PATH = Path(__file__).parent / "assets" / "logo_header_v.png"
_LOGO_DATA_URI = "data:image/png;base64," + base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")


def render_watch_page(filename: str, video_url: str) -> str:
    """Monta a página de player + download para um vídeo gravado.

    Página autocontida (sem dependências novas nem template engine) pensada
    para ser aberta a partir do QR code gerado por /api/recording/getvideo,
    quase sempre em um celular.
    """
    safe_filename = escape(filename)
    safe_video_url = escape(video_url)

    return f"""<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Seu vídeo está pronto</title>
<style>
  :root {{
    --bg: #051615;
    --bg-glow-1: #004c49;
    --bg-glow-2: #007e7a;
    --accent-mint: #0abb98;
    --accent-gold: #ffb347;
    --text: #f2fdf6;
  }}

  * {{ box-sizing: border-box; }}

  html, body {{
    height: 100%;
  }}

  body {{
    margin: 0;
    height: 100dvh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: var(--text);
    background: var(--bg);
    background-image:
      radial-gradient(circle at 20% 15%, rgba(0, 126, 122, 0.5), transparent 55%),
      radial-gradient(circle at 85% 80%, rgba(10, 187, 152, 0.3), transparent 50%);
    background-attachment: fixed;
  }}

  header.site-header {{
    flex: 0 0 auto;
    display: flex;
    justify-content: center;
    padding: 20px 24px 0;
  }}

  .logo {{
    display: block;
    height: 144px;
    width: auto;
  }}

  main.content {{
    flex: 1 1 auto;
    min-height: 0;
    display: flex;
    justify-content: center;
    padding: 10px 24px 16px;
  }}

  .card {{
    width: 100%;
    max-width: 420px;
    min-height: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 18px;
  }}

  h1 {{
    flex: 0 0 auto;
    margin: 0;
    font-size: 1.15rem;
    font-weight: 600;
    text-align: center;
  }}

  video {{
    flex: 0 0 auto;
    align-self: center;
    height: 42vh;
    aspect-ratio: 9 / 16;
    object-fit: contain;
    border-radius: 16px;
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08), 0 12px 40px rgba(0, 126, 122, 0.4);
  }}

  .actions {{
    flex: 0 0 auto;
    display: flex;
    gap: 12px;
  }}

  a.download,
  button.share {{
    flex: 1;
    display: block;
    text-align: center;
    text-decoration: none;
    padding: 12px 20px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.95rem;
    font-family: inherit;
    cursor: pointer;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
  }}

  a.download {{
    color: var(--text);
    border: none;
    background: linear-gradient(135deg, var(--accent-mint), var(--bg-glow-1) 45%, var(--bg-glow-2));
    box-shadow: 0 8px 24px rgba(0, 126, 122, 0.35);
  }}

  a.download:hover,
  a.download:focus-visible {{
    box-shadow: 0 8px 28px rgba(255, 179, 71, 0.45);
    transform: translateY(-1px);
  }}

  a.download:active {{
    transform: translateY(0);
  }}

  button.share {{
    color: var(--text);
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(0, 126, 122, 0.6);
  }}

  button.share:hover,
  button.share:focus-visible {{
    border-color: var(--accent-gold);
    transform: translateY(-1px);
  }}

  button.share:active {{
    transform: translateY(0);
  }}

  button.share[hidden] {{
    display: none;
  }}
</style>
</head>
<body>
  <header class="site-header">
    <img class="logo" src="{_LOGO_DATA_URI}" alt="ECCO">
  </header>
  <main class="content">
    <div class="card">
      <h1>Seu vídeo está pronto</h1>
      <video id="video" src="{safe_video_url}" controls playsinline preload="metadata"></video>
      <div class="actions">
        <a class="download" id="download-link" href="{safe_video_url}" download="{safe_filename}">Baixar vídeo</a>
        <button type="button" class="share" id="share-btn" hidden>Compartilhar</button>
      </div>
    </div>
  </main>
  <script>
    (function () {{
      var video = document.getElementById('video');
      var downloadLink = document.getElementById('download-link');
      var shareBtn = document.getElementById('share-btn');
      var shareBtnDefaultLabel = shareBtn.textContent;

      function logWatchEvent(action) {{
        try {{
          fetch('/watch/{safe_filename}/event', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ action: action }}),
            keepalive: true
          }});
        }} catch (e) {{}}
      }}

      downloadLink.addEventListener('click', function () {{
        logWatchEvent('download');
      }});

      function canShareFiles() {{
        if (!navigator.share || !navigator.canShare) return false;
        try {{
          var probe = new File([''], 'probe.mp4', {{ type: 'video/mp4' }});
          return navigator.canShare({{ files: [probe] }});
        }} catch (e) {{
          return false;
        }}
      }}

      if (canShareFiles()) {{
        shareBtn.hidden = false;
      }}

      shareBtn.addEventListener('click', async function () {{
        try {{
          var response = await fetch(video.currentSrc || video.src);
          var blob = await response.blob();
          var file = new File([blob], '{safe_filename}', {{ type: blob.type || 'video/mp4' }});

          await navigator.share({{
            files: [file],
            title: 'Meu vídeo',
            text: 'Confira meu vídeo!'
          }});
          logWatchEvent('share');
        }} catch (error) {{
          if (error && error.name === 'AbortError') return;
          console.error('Erro ao compartilhar:', error);
          shareBtn.textContent = 'Falha ao compartilhar';
          setTimeout(function () {{
            shareBtn.textContent = shareBtnDefaultLabel;
          }}, 2000);
        }}
      }});
    }})();
  </script>
</body>
</html>"""
