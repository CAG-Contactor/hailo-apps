# Pose Logger Application

Denna applikation är en variant av `pose_estimation` som **inte renderar någon streckgubbe** (skelett-overlay) eller fönster som standard. Istället körs applikationen resurssnålt i headless-läge (med GStreamers `fakesink`) och loggar det fullständiga underlaget för streckgubben (alla 17 anatomiska keypoints med koordinater och konfidens) till loggen.

Applikationen använder samma Hailo-modeller som pose estimation (`yolov8s_pose` för Hailo-8L och `yolov8m_pose` för Hailo-8).

---

## Körning

### Standardkörning (Headless / Ren dataloggning):
```bash
python hailo_apps/python/pipeline_apps/pose_logger/pose_logger.py --input usb
```
Eller med Raspberry Pi-kamera:
```bash
python hailo_apps/python/pipeline_apps/pose_logger/pose_logger.py --input rpi
```
Eller mot en videofil:
```bash
python hailo_apps/python/pipeline_apps/pose_logger/pose_logger.py --input /path/to/video.mp4
```

---

## Tillvalsflaggor

* `--show-video`: Öppnar videofönstret men visar **ren video utan streckgubbe/overlay**. Användbart om man vill inspektera kamerabilden utan att skymma motivet med grafik.
* `--log-format [json|text]`:
  * `json` (standard): Skriver ut en rad JSON per bildruta med fullständig metadata. Perfekt för datainsamling, pipelines, MQTT, etc.
  * `text`: Skriver ut formaterad, lättläst text i terminalen per detekterad person och led.

### Exempel med textformat:
```bash
python hailo_apps/python/pipeline_apps/pose_logger/pose_logger.py --input usb --log-format text
```

### Exempel med ren videovisning:
```bash
python hailo_apps/python/pipeline_apps/pose_logger/pose_logger.py --input usb --show-video
```

---

## Loggformat

### 1. JSON-format (`--log-format json`)
```json
{
  "frame_count": 42,
  "video_width": 1280,
  "video_height": 720,
  "persons": [
    {
      "track_id": 1,
      "label": "person",
      "confidence": 0.88,
      "bbox": {
        "xmin": 0.32,
        "ymin": 0.15,
        "width": 0.25,
        "height": 0.70,
        "pixels": { "xmin": 409, "ymin": 108, "xmax": 729, "ymax": 612 }
      },
      "keypoints": {
        "nose": { "x": 0.441, "y": 0.210, "pixel_x": 564, "pixel_y": 151, "confidence": 0.94 },
        "left_eye": { "x": 0.453, "y": 0.198, "pixel_x": 579, "pixel_y": 142, "confidence": 0.91 },
        "right_eye": { "x": 0.428, "y": 0.201, "pixel_x": 547, "pixel_y": 144, "confidence": 0.92 },
        "left_ear": { "x": 0.472, "y": 0.215, "pixel_x": 604, "pixel_y": 154, "confidence": 0.86 },
        "right_ear": { "x": 0.415, "y": 0.218, "pixel_x": 531, "pixel_y": 156, "confidence": 0.84 },
        "left_shoulder": { "x": 0.501, "y": 0.312, "pixel_x": 641, "pixel_y": 224, "confidence": 0.89 },
        "right_shoulder": { "x": 0.392, "y": 0.319, "pixel_x": 501, "pixel_y": 229, "confidence": 0.91 },
        "left_elbow": { "x": 0.525, "y": 0.445, "pixel_x": 672, "pixel_y": 320, "confidence": 0.82 },
        "right_elbow": { "x": 0.368, "y": 0.451, "pixel_x": 471, "pixel_y": 324, "confidence": 0.85 },
        "left_wrist": { "x": 0.539, "y": 0.562, "pixel_x": 690, "pixel_y": 404, "confidence": 0.78 },
        "right_wrist": { "x": 0.351, "y": 0.570, "pixel_x": 449, "pixel_y": 410, "confidence": 0.80 },
        "left_hip": { "x": 0.475, "y": 0.582, "pixel_x": 608, "pixel_y": 419, "confidence": 0.87 },
        "right_hip": { "x": 0.408, "y": 0.585, "pixel_x": 522, "pixel_y": 421, "confidence": 0.88 },
        "left_knee": { "x": 0.481, "y": 0.745, "pixel_x": 615, "pixel_y": 536, "confidence": 0.84 },
        "right_knee": { "x": 0.412, "y": 0.751, "pixel_x": 527, "pixel_y": 540, "confidence": 0.85 },
        "left_ankle": { "x": 0.488, "y": 0.895, "pixel_x": 624, "pixel_y": 644, "confidence": 0.81 },
        "right_ankle": { "x": 0.419, "y": 0.902, "pixel_x": 536, "pixel_y": 649, "confidence": 0.79 }
      }
    }
  ]
}
```

### 2. Textformat (`--log-format text`)
```text
--- Frame 42 (1280x720) | Antal personer: 1 ---
Person [ID: 1, Konfidens: 0.88, Box: (409,108)-(729,612)]
  nose            : ( 564px,  151px)  konfidens: 0.94
  left_eye        : ( 579px,  142px)  konfidens: 0.91
  right_eye       : ( 547px,  144px)  konfidens: 0.92
  left_ear        : ( 604px,  154px)  konfidens: 0.86
  right_ear       : ( 531px,  156px)  konfidens: 0.84
  left_shoulder   : ( 641px,  224px)  konfidens: 0.89
  right_shoulder  : ( 501px,  229px)  konfidens: 0.91
  left_elbow      : ( 672px,  320px)  konfidens: 0.82
  right_elbow     : ( 471px,  324px)  konfidens: 0.85
  left_wrist      : ( 690px,  404px)  konfidens: 0.78
  right_wrist     : ( 449px,  410px)  konfidens: 0.80
  left_hip        : ( 608px,  419px)  konfidens: 0.87
  right_hip       : ( 522px,  421px)  konfidens: 0.88
  left_knee       : ( 615px,  536px)  konfidens: 0.84
  right_knee      : ( 527px,  540px)  konfidens: 0.85
  left_ankle      : ( 624px,  644px)  konfidens: 0.81
  right_ankle     : ( 536px,  649px)  konfidens: 0.79
```
