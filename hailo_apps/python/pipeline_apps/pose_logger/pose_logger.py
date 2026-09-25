# region imports
import json
import os
import socket

os.environ["GST_PLUGIN_FEATURE_RANK"] = "vaapidecodebin:NONE"

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

import hailo
from hailo_apps.python.core.common.buffer_utils import get_caps_from_pad
from hailo_apps.python.core.common.hailo_logger import get_logger
from hailo_apps.python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.python.pipeline_apps.pose_logger.pose_logger_pipeline import (
    GStreamerPoseLoggerApp,
    get_pose_logger_parser,
)

hailo_logger = get_logger(__name__)
# endregion imports

# Standard 17 COCO keypoints ordnade efter index
KEYPOINTS = [
    "nose",            # 0
    "left_eye",        # 1
    "right_eye",       # 2
    "left_ear",        # 3
    "right_ear",       # 4
    "left_shoulder",   # 5
    "right_shoulder",  # 6
    "left_elbow",      # 7
    "right_elbow",     # 8
    "left_wrist",      # 9
    "right_wrist",     # 10
    "left_hip",        # 11
    "right_hip",       # 12
    "left_knee",       # 13
    "right_knee",      # 14
    "left_ankle",      # 15
    "right_ankle",     # 16
]


# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.log_format = "json"
        self.udp_port = 5005
        self.broadcast_address = "255.255.255.255"
        self.no_log = False
        self.sock = None
        self.udp_enabled = False

    def init_udp(self):
        """Initierar UDP-socket med broadcast aktiverat."""
        if self.udp_port > 0:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                self.udp_enabled = True
                hailo_logger.info(
                    "UDP broadcast aktiverat till %s:%d", self.broadcast_address, self.udp_port
                )
            except OSError as e:
                hailo_logger.error("Kunde inte skapa UDP broadcast-socket: %s", e)
                self.udp_enabled = False
        else:
            self.udp_enabled = False

    def broadcast_pose_data(self, data_dict: dict):
        """Skickar pose-data som JSON-datagram via UDP-broadcast."""
        if not self.udp_enabled or self.sock is None:
            return
        try:
            payload = json.dumps(data_dict).encode("utf-8")
            self.sock.sendto(payload, (self.broadcast_address, self.udp_port))
        except OSError as e:
            hailo_logger.warning("Fel vid UDP broadcast: %s", e)


# -----------------------------------------------------------------------------------------------
# User-defined callback function
# -----------------------------------------------------------------------------------------------
def app_callback(element, buffer, user_data):
    """
    Callback som anropas för varje videobuffert.
    Extraherar landmärken (underlaget för streckgubben) och loggar datat utan rendering.
    """
    hailo_logger.debug("Callback triggered. Current frame count=%d", user_data.get_count())

    if buffer is None:
        hailo_logger.warning("Received None buffer.")
        return

    frame_count = user_data.get_count()
    pad = element.get_static_pad("src")
    _, width, height = get_caps_from_pad(pad)
    width = width or 1280
    height = height or 720

    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    persons = []

    for detection in detections:
        label = detection.get_label()
        if label != "person":
            continue

        track_id = None
        track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
        if len(track) == 1:
            track_id = track[0].get_id()

        bbox = detection.get_bbox()
        confidence = float(detection.get_confidence())

        person_data = {
            "track_id": track_id,
            "label": label,
            "confidence": round(confidence, 3),
            "bbox": {
                "xmin": round(float(bbox.xmin()), 4),
                "ymin": round(float(bbox.ymin()), 4),
                "width": round(float(bbox.width()), 4),
                "height": round(float(bbox.height()), 4),
                "pixels": {
                    "xmin": int(bbox.xmin() * width),
                    "ymin": int(bbox.ymin() * height),
                    "xmax": int((bbox.xmin() + bbox.width()) * width),
                    "ymax": int((bbox.ymin() + bbox.height()) * height),
                },
            },
            "keypoints": {},
        }

        # Extrahera de 17 punkterna som utgör streckgubbens anatomi
        landmarks = detection.get_objects_typed(hailo.HAILO_LANDMARKS)
        if landmarks:
            points = landmarks[0].get_points()
            for idx, point in enumerate(points):
                if idx < len(KEYPOINTS):
                    name = KEYPOINTS[idx]
                    # Beräkna globala normaliserade koordinater
                    global_norm_x = point.x() * bbox.width() + bbox.xmin()
                    global_norm_y = point.y() * bbox.height() + bbox.ymin()

                    # Beräkna pixelkoordinater
                    pixel_x = int(global_norm_x * width)
                    pixel_y = int(global_norm_y * height)

                    person_data["keypoints"][name] = {
                        "x": round(float(global_norm_x), 4),
                        "y": round(float(global_norm_y), 4),
                        "pixel_x": pixel_x,
                        "pixel_y": pixel_y,
                        "confidence": round(float(point.confidence()), 3),
                    }

        persons.append(person_data)

    # Hantera detekterade personer
    if persons:
        output = {
            "frame_count": frame_count,
            "video_width": width,
            "video_height": height,
            "persons": persons,
        }

        # 1. Skicka via UDP-broadcast till alla lyssnande klienter på nätverket
        user_data.broadcast_pose_data(output)

        # 2. Skriv ut lokalt på loggen/konsolen om ej --no-log är satt
        if not getattr(user_data, "no_log", False):
            log_format = getattr(user_data, "log_format", "json")
            if log_format == "json":
                hailo_logger.info("POSE_DATA: %s", json.dumps(output))
            else:
                lines = [
                    f"\n--- Frame {frame_count} ({width}x{height}) | Antal personer: {len(persons)} ---"
                ]
                for p in persons:
                    b = p["bbox"]["pixels"]
                    track_str = f"ID: {p['track_id']}, " if p["track_id"] is not None else ""
                    lines.append(
                        f"Person [{track_str}Konfidens: {p['confidence']:.2f}, Box: ({b['xmin']},{b['ymin']})-({b['xmax']},{b['ymax']})]"
                    )
                    for kp_name, kp in p["keypoints"].items():
                        lines.append(
                            f"  {kp_name:<16}: ({kp['pixel_x']:>4}px, {kp['pixel_y']:>4}px)  konfidens: {kp['confidence']:.2f}"
                        )
                hailo_logger.info("\n".join(lines))


def main():
    hailo_logger.info("Starting Pose Logger App.")
    parser = get_pose_logger_parser()
    user_data = user_app_callback_class()
    app = GStreamerPoseLoggerApp(app_callback, user_data, parser=parser)
    app.run()


if __name__ == "__main__":
    main()
