"""Página HTML de visualização/download do vídeo gravado (servida em /watch/{filename})"""

from html import escape


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
    --bg: #0a0612;
    --bg-glow-1: #6d28d9;
    --bg-glow-2: #c026d3;
    --accent-blue: #5b7cfa;
    --accent-gold: #ffb347;
    --text: #f5f3ff;
    --text-muted: #b8a9d9;
  }}

  * {{ box-sizing: border-box; }}

  body {{
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: var(--text);
    background: var(--bg);
    background-image:
      radial-gradient(circle at 20% 15%, rgba(109, 40, 217, 0.45), transparent 55%),
      radial-gradient(circle at 85% 80%, rgba(192, 38, 212, 0.35), transparent 50%);
    background-attachment: fixed;
  }}

  .card {{
    width: 100%;
    max-width: 480px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }}

  h1 {{
    margin: 0;
    font-size: 1.4rem;
    font-weight: 600;
    text-align: center;
  }}

  p.subtitle {{
    margin: -12px 0 0;
    text-align: center;
    color: var(--text-muted);
    font-size: 0.92rem;
  }}

  video {{
    width: 100%;
    border-radius: 16px;
    background: #000;
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08), 0 12px 40px rgba(109, 40, 217, 0.35);
  }}

  .actions {{
    display: flex;
    gap: 12px;
  }}

  a.download,
  button.share {{
    flex: 1;
    display: block;
    text-align: center;
    text-decoration: none;
    padding: 14px 20px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 1rem;
    font-family: inherit;
    cursor: pointer;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
  }}

  a.download {{
    color: var(--text);
    border: none;
    background: linear-gradient(135deg, var(--accent-blue), var(--bg-glow-1) 45%, var(--bg-glow-2));
    box-shadow: 0 8px 24px rgba(192, 38, 212, 0.35);
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
    border: 1px solid rgba(192, 38, 212, 0.6);
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
  <div class="card">
    <h1>Seu vídeo está pronto 🎬</h1>
    <p class="subtitle">Assista abaixo ou baixe para guardar no seu dispositivo</p>
    <video id="video" src="{safe_video_url}" controls playsinline preload="metadata"></video>
    <div class="actions">
      <a class="download" href="{safe_video_url}" download="{safe_filename}">Baixar vídeo</a>
      <button type="button" class="share" id="share-btn" hidden>Compartilhar</button>
    </div>
  </div>
  <script>
    (function () {{
      var video = document.getElementById('video');
      var shareBtn = document.getElementById('share-btn');
      var shareBtnDefaultLabel = shareBtn.textContent;

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
