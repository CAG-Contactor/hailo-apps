# region imports
import argparse
import setproctitle

from hailo_apps.python.core.common.core import (
    get_pipeline_parser,
    get_resource_path,
    handle_list_models_flag,
    resolve_hef_path,
)
from hailo_apps.python.core.common.defines import (
    POSE_ESTIMATION_PIPELINE,
    POSE_ESTIMATION_POSTPROCESS_FUNCTION,
    POSE_ESTIMATION_POSTPROCESS_SO_FILENAME,
    RESOURCES_SO_DIR_NAME,
)
from hailo_apps.python.core.common.hailo_logger import get_logger
from hailo_apps.python.core.gstreamer.gstreamer_app import (
    GStreamerApp,
    app_callback_class,
    dummy_callback,
)
from hailo_apps.python.core.gstreamer.gstreamer_helper_pipelines import (
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    QUEUE,
    TRACKER_PIPELINE,
    USER_CALLBACK_PIPELINE,
)

hailo_logger = get_logger(__name__)
# endregion imports

POSE_LOGGER_APP_TITLE = "Hailo Pose Logger App"


def get_pose_logger_parser() -> argparse.ArgumentParser:
    """
    Argument parser för Pose Logger. Utökar standardpipelinen med alternativ
    för visning och loggformat.
    """
    parser = get_pipeline_parser()
    parser.add_argument(
        "--show-video",
        action="store_true",
        default=False,
        help="Visa videofönster utan streckgubbe/overlay (standard är headless med fakesink).",
    )
    parser.add_argument(
        "--log-format",
        choices=["json", "text"],
        default="json",
        help="Utmatningsformat på loggen: 'json' (strukturerad JSON per frame) eller 'text' (radvis läsbar text). Standard: json.",
    )
    return parser


# -----------------------------------------------------------------------------------------------
# User Gstreamer Application
# -----------------------------------------------------------------------------------------------
class GStreamerPoseLoggerApp(GStreamerApp):
    def __init__(self, app_callback, user_data, parser=None):
        if parser is None:
            parser = get_pose_logger_parser()

        # Hantera --list-models flagga
        handle_list_models_flag(parser, POSE_ESTIMATION_PIPELINE)

        hailo_logger.info("Initializing GStreamer Pose Logger App...")

        super().__init__(parser, user_data)
        hailo_logger.debug("Parser initialized, user_data ready.")

        # Batch size
        if self.batch_size == 1:
            self.batch_size = 2

        hailo_logger.debug(
            "Video params set: %dx%d, batch_size=%d",
            self.video_width,
            self.video_height,
            self.batch_size,
        )

        # HEF och post-process bibliotek från pose estimation
        self.hef_path = resolve_hef_path(
            self.hef_path,
            app_name=POSE_ESTIMATION_PIPELINE,
            arch=self.arch,
        )
        hailo_logger.debug("Using HEF path: %s", self.hef_path)

        self.app_callback = app_callback
        self.post_process_so = get_resource_path(
            POSE_ESTIMATION_PIPELINE,
            RESOURCES_SO_DIR_NAME,
            self.arch,
            POSE_ESTIMATION_POSTPROCESS_SO_FILENAME,
        )
        self.post_process_function = POSE_ESTIMATION_POSTPROCESS_FUNCTION
        hailo_logger.debug(
            "Post-process SO: %s, Function: %s", self.post_process_so, self.post_process_function
        )

        self.show_video = getattr(self.options_menu, "show_video", False)
        self.log_format = getattr(self.options_menu, "log_format", "json")
        user_data.log_format = self.log_format

        setproctitle.setproctitle(POSE_LOGGER_APP_TITLE)
        hailo_logger.debug("Process title set: %s", POSE_LOGGER_APP_TITLE)

        self.create_pipeline()
        hailo_logger.info("Pipeline created successfully.")

    def get_pipeline_string(self):
        hailo_logger.debug("Building pipeline string...")
        source_pipeline = self.get_source_pipeline()
        infer_pipeline = INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.post_process_so,
            post_function_name=self.post_process_function,
            batch_size=self.batch_size,
        )
        infer_pipeline_wrapper = INFERENCE_PIPELINE_WRAPPER(infer_pipeline)
        tracker_pipeline = TRACKER_PIPELINE(class_id=0)
        user_callback_pipeline = USER_CALLBACK_PIPELINE()

        if self.show_video:
            # Visa ren video utan hailooverlay (ingen streckgubbe)
            sink_pipeline = (
                f"{QUEUE(name='display_videoconvert_q')} ! "
                f"videoconvert name=display_videoconvert n-threads=2 qos=false ! "
                f"{QUEUE(name='display_q')} ! "
                f"fpsdisplaysink name=display_sink video-sink={self.video_sink} sync={self.sync} "
                f"text-overlay={self.show_fps} signal-fps-measurements=true"
            )
        else:
            # Headless läge: ingen rendering, frames slängs till fakesink efter callback
            sink_pipeline = f"{QUEUE(name='fakesink_q')} ! fakesink sync={self.sync}"

        pipeline_string = (
            f"{source_pipeline} ! "
            f"{infer_pipeline_wrapper} ! "
            f"{tracker_pipeline} ! "
            f"{user_callback_pipeline} ! "
            f"{sink_pipeline}"
        )
        hailo_logger.debug("Pipeline string: %s", pipeline_string)
        return pipeline_string


def main():
    hailo_logger.info("Starting Pose Logger App main()...")
    user_data = app_callback_class()
    app = GStreamerPoseLoggerApp(dummy_callback, user_data)
    app.run()


if __name__ == "__main__":
    hailo_logger.info("Launching Pose Logger App...")
    main()
