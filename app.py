import time
import numpy as np
from flask import Flask, Response, request

app = Flask(__name__)

# ---------- параметры пончика ----------
screen_size = 40
theta_spacing = 0.07
phi_spacing = 0.02
illumination = np.fromiter(".,-~:;=!*#$@", dtype="<U1")

R1 = 1
R2 = 2
K2 = 5
K1 = screen_size * K2 * 3 / (8 * (R1 + R2))

# ---------- управляемая скорость ----------
DEFAULT_FPS = 20
MIN_FPS = 1
MAX_FPS = 120
frame_delay = 1.0 / DEFAULT_FPS  # глобальная, меняется через /speed


# ---------- рендер кадра ----------
def render_frame(A: float, B: float) -> str:
    cos_A, sin_A = np.cos(A), np.sin(A)
    cos_B, sin_B = np.cos(B), np.sin(B)

    output = np.full((screen_size, screen_size), " ")
    zbuffer = np.zeros((screen_size, screen_size))

    cos_phi = np.cos(phi := np.arange(0, 2 * np.pi, phi_spacing))
    sin_phi = np.sin(phi)
    cos_theta = np.cos(theta := np.arange(0, 2 * np.pi, theta_spacing))
    sin_theta = np.sin(theta)
    circle_x = R2 + R1 * cos_theta
    circle_y = R1 * sin_theta

    x = (np.outer(cos_B * cos_phi + sin_A * sin_B * sin_phi, circle_x) - circle_y * cos_A * sin_B).T
    y = (np.outer(sin_B * cos_phi - sin_A * cos_B * sin_phi, circle_x) + circle_y * cos_A * cos_B).T
    z = ((K2 + cos_A * np.outer(sin_phi, circle_x)) + circle_y * sin_A).T
    ooz = np.reciprocal(z)
    xp = (screen_size / 2 + K1 * ooz * x).astype(int)
    yp = (screen_size / 2 - K1 * ooz * y).astype(int)
    L1 = (((np.outer(cos_phi, cos_theta) * sin_B) - cos_A * np.outer(sin_phi, cos_theta)) - sin_A * sin_theta)
    L2 = cos_B * (cos_A * sin_theta - np.outer(sin_phi, cos_theta * sin_A))
    L = np.around(((L1 + L2) * 8)).astype(int).T
    mask_L = L >= 0
    chars = illumination[L]

    for i in range(90):
        mask = mask_L[i] & (ooz[i] > zbuffer[xp[i], yp[i]])
        zbuffer[xp[i], yp[i]] = np.where(mask, ooz[i], zbuffer[xp[i], yp[i]])
        output[xp[i], yp[i]] = np.where(mask, chars[i], output[xp[i], yp[i]])

    return "\n".join(" ".join(row) for row in output)


# ---------- SSE-стрим ----------
def frame_stream():
    global frame_delay
    A, B = 1.0, 1.0
    while True:
        frame = render_frame(A, B)
        payload = "\n".join(f"data: {line}" for line in frame.split("\n"))
        yield payload + "\n\n"

        A += theta_spacing
        B += phi_spacing
        time.sleep(frame_delay)  # читаем актуальное значение


# ---------- HTML ----------
HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>THE ПОНЧИК 🍩</title>
  <style>
    html, body {
      margin: 0;
      height: 100%;
      background: #000;
      color: #0f0;
      overflow: hidden;
      font-family: "Courier New", monospace;
    }
    body {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 20px;
    }
    h1 {
      margin: 0;
      font-size: clamp(28px, 8vw, 96px);
      letter-spacing: 0.1em;
      font-weight: 900;
      color: #0f0;
      text-shadow: 0 0 10px #0f0, 0 0 30px #0f0, 0 0 60px #0f0;
      text-align: center;
      white-space: nowrap;
    }
    #donut-wrap {
      display: flex;
      align-items: center;
      justify-content: center;
    }
    #donut {
      margin: 0;
      padding: 0;
      font-family: "Courier New", monospace;
      font-size: 14px;
      line-height: 1;
      white-space: pre;
      text-shadow: 0 0 4px #0f0;
    }

    /* блок с ползунком */
    #speed-wrap {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      color: #0f0;
      font-size: 14px;
      text-shadow: 0 0 4px #0f0;
    }
    #speed {
      width: 240px;
      accent-color: #0f0;   /* цвет ползунка в современных браузерах */
      cursor: pointer;
    }
    #speed-value {
      font-weight: bold;
    }
  </style>
</head>
<body>
  <h1>THE ПОНЧИК</h1>

  <div id="donut-wrap">
    <pre id="donut">подключаюсь...</pre>
  </div>

  <div id="speed-wrap">
    <label for="speed">
      Скорость: <span id="speed-value">20</span> FPS
    </label>
    <input id="speed" type="range" min="1" max="120" value="20" step="1">
  </div>

  <script>
    // ---------- стрим пончика ----------
    const el = document.getElementById("donut");
    const es = new EventSource("/stream");
    let buffer = "";

    es.onmessage = (event) => {
      buffer += event.data + "\\n";
      const lines = buffer.split("\\n");
      if (lines.length >= 40) {
        el.textContent = lines.slice(0, 40).join("\\n");
        buffer = lines.slice(40).join("\\n");
      }
    };
    es.onerror = () => {
      el.textContent = "соединение потеряно, переподключаюсь...";
    };

    // ---------- ползунок скорости ----------
    const slider = document.getElementById("speed");
    const label = document.getElementById("speed-value");

    let pending = null;   // чтобы не спамить сервер
    let scheduled = false;

    function sendSpeed() {
      const fps = slider.value;
      label.textContent = fps;
      if (scheduled) {
        pending = fps;
        return;
      }
      scheduled = true;
      fetch(`/speed?fps=${fps}`, { method: "POST" })
        .catch(() => {})
        .finally(() => {
          scheduled = false;
          if (pending !== null && pending !== slider.value) {
            const next = pending;
            pending = null;
            slider.value = next;
            sendSpeed();
          }
        });
    }

    slider.addEventListener("input", sendSpeed);
  </script>
</body>
</html>
"""


# ---------- маршруты ----------
@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")


@app.route("/stream")
def stream():
    return Response(
        frame_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/speed", methods=["POST"])
def set_speed():
    global frame_delay
    try:
        fps = float(request.args.get("fps", DEFAULT_FPS))
    except ValueError:
        return {"ok": False, "error": "fps must be a number"}, 400

    fps = max(MIN_FPS, min(MAX_FPS, fps))
    frame_delay = 1.0 / fps
    return {"ok": True, "fps": fps}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)