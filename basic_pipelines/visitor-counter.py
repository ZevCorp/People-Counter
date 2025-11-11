import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import argparse
import multiprocessing
import numpy as np
import setproctitle
import cv2
import time
import hailo
import supervision as sv
from pathlib import Path
from hailo_rpi_common import (
  get_default_parser,
  QUEUE,
  get_caps_from_pad,
  get_numpy_from_buffer,
  GStreamerApp,
  app_callback_class,
)
# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
# Inheritance from the app_callback_class
class user_app_callback_class(app_callback_class):
  def __init__(self):
    super().__init__()
    self.new_variable = 42 # New variable example
 
  def new_function(self): # New function example
    return "The meaning of life is: "
# -----------------------------------------------------------------------------------------------
# User-defined callback function
# -----------------------------------------------------------------------------------------------
# This is the callback function that will be called when data is available from the pipeline
def app_callback(pad, info, user_data):
  buffer = info.get_buffer()
  if buffer is None:
    return Gst.PadProbeReturn.OK
  format, width, height = get_caps_from_pad(pad)
  if format is None or width is None or height is None:
    print("Failed to get format, width, or height from pad")
    return Gst.PadProbeReturn.OK
  # If the user_data.use_frame is set to True, we can get the video frame from the buffer
  frame = None
  if user_data.use_frame and format is not None and width is not None and height is not None:
    # Get video frame
    frame = get_numpy_from_buffer(buffer, format, width, height)
  roi = hailo.get_roi_from_buffer(buffer)
  hailo_detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
  n = len(hailo_detections)
  boxes = np.zeros((n, 4))
  confidence = np.zeros(n)
  class_id = np.zeros(n)
  tracker_id = np.empty(n)
  for i, detection in enumerate(hailo_detections):
    class_id[i] = detection.get_class_id()
    confidence[i] = detection.get_confidence()
    tracker_id[i] = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)[0].get_id()
    bbox = detection.get_bbox()
    boxes[i] = [bbox.xmin() * width, bbox.ymin() * height, bbox.xmax() * width, bbox.ymax() * height]
  detections = sv.Detections(
      xyxy=boxes,
      confidence=confidence,
      class_id=class_id,
      tracker_id=tracker_id)
  line_zone.trigger(detections)
  textoverlay_top = app.pipeline.get_by_name("hailo_text_top")
  textoverlay_bottom = app.pipeline.get_by_name("hailo_text_bottom")
  textoverlay_top.set_property('text', f'\u2190 IN: {line_zone.in_count} \u2190')
  textoverlay_bottom.set_property('text', f'\u2192 OUT: {line_zone.out_count} \u2192')
  textoverlay_top.set_property('font-desc', 'Monospace 25')
  textoverlay_bottom.set_property('font-desc', 'Monospace 25')
  if user_data.use_frame:
      # Draw a line on the frame
      start_point = (320, 0) # Start point of the line (x, y)
      end_point = (320, 640)  # End point of the line (x, y)
      color = (0, 255, 0)    # Line color in BGR (Blue, Green, Red)
      thickness = 2       # Line thickness
      # Draw the line
      cv2.line(frame, start_point, end_point, color, thickness)
      cv2.imwrite('/home/raspberry/output_frame.jpg', frame)     
      # Convert the frame to BGR
      frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
      user_data.set_frame(frame)
  return Gst.PadProbeReturn.OK
# -----------------------------------------------------------------------------------------------
# Custom RTSP Detection App for Visitor Counter
# -----------------------------------------------------------------------------------------------
class RTSPGStreamerDetectionApp(GStreamerApp):
  def __init__(self, args, user_data, rtsp_url):
    # Assign rtsp_url BEFORE calling parent constructor
    # because parent calls get_pipeline_string() during initialization
    self.rtsp_url = rtsp_url
    print(f"🎯 Configurando pipeline RTSP personalizado para: {rtsp_url}")
    super().__init__(args, user_data)
    # Additional initialization code can be added here
    # Set Hailo parameters these parameters should be set based on the model used
    self.batch_size = 1
    self.network_width = 640
    self.network_height = 640
    self.network_format = "RGB"
    nms_score_threshold = 0.3
    nms_iou_threshold = 0.45
    # Temporary code: new postprocess will be merged to TAPPAS.
    # Check if new postprocess so file exists
    new_postprocess_path = os.path.join(self.current_path, '../resources/libyolo_hailortpp_post.so')
    if os.path.exists(new_postprocess_path):
      self.default_postprocess_so = new_postprocess_path
    else:
      self.default_postprocess_so = os.path.join(self.postprocess_dir, 'libyolo_hailortpp_post.so')
    if args.hef_path is not None:
      self.hef_path = args.hef_path
    # Set the HEF file path based on the network
    elif args.network == "yolov6n":
      self.hef_path = os.path.join(self.current_path, '../resources/yolov6n.hef')
    elif args.network == "yolov8s":
      self.hef_path = os.path.join(self.current_path, '../resources/yolov8s_h8l.hef')
    elif args.network == "yolox_s_leaky":
      self.hef_path = os.path.join(self.current_path, '../resources/yolox_s_leaky_h8l_mz.hef')
    else:
      assert False, "Invalid network type"
    # User-defined label JSON file
    if args.labels_json is not None:
      self.labels_config = f' config-path={args.labels_json} '
      # Temporary code
      if not os.path.exists(new_postprocess_path):
        print("New postprocess so file is missing. It is required to support custom labels. Check documentation for more information.")
        exit(1)
    else:
      self.labels_config = ''
    self.app_callback = app_callback
    self.thresholds_str = (
      f"nms-score-threshold={nms_score_threshold} "
      f"nms-iou-threshold={nms_iou_threshold} "
      f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
    )
    # Set the process title
    setproctitle.setproctitle("booth visitor counter")
    self.create_pipeline()

  def get_pipeline_string(self):
    """
    Custom pipeline that uses rtspsrc - COMPATIBLE con detection.py exitoso
    """
    print(f"🔧 Construyendo pipeline RTSP personalizado...")
    
    # Pipeline RTSP basado en detection.py que SÍ FUNCIONA
    complete_rtsp_pipeline = (
        f'rtspsrc location="{self.rtsp_url}" protocols=tcp latency=300 '
        f'! rtph264depay '
        f'! h264parse '
        f'! avdec_h264 '
        + QUEUE("source_queue_decode", leaky="no", max_size_buffers=3)
        + '! videoscale name=source_videoscale n-threads=2 '
        + QUEUE("source_convert_q", leaky="no", max_size_buffers=3)
        + '! videoconvert n-threads=3 name=source_convert qos=false '
        + f'! video/x-raw, pixel-aspect-ratio=1/1, format={self.network_format}, width={self.network_width}, height={self.network_height} '
        + '! videorate name=source_videorate '
        + f'! capsfilter name=source_fps_caps caps="video/x-raw, framerate=30/1" '
        + QUEUE("inference_wrapper_input_q", leaky="no", max_size_buffers=3)
        + '! hailocropper name=inference_wrapper_crop so-path=/usr/lib/aarch64-linux-gnu/hailo/tappas/post_processes/cropping_algorithms/libwhole_buffer.so function-name=create_crops use-letterbox=true resize-method=inter-area internal-offset=true '
        + 'hailoaggregator name=inference_wrapper_agg '
        + 'inference_wrapper_crop. '
        + QUEUE("inference_wrapper_bypass_q", leaky="no", max_size_buffers=20)
        + '! inference_wrapper_agg.sink_0 '
        + 'inference_wrapper_crop. '
        + QUEUE("inference_scale_q", leaky="no", max_size_buffers=3)
        + '! videoscale name=inference_videoscale n-threads=2 qos=false '
        + QUEUE("inference_convert_q", leaky="no", max_size_buffers=3)
        + '! video/x-raw, pixel-aspect-ratio=1/1 '
        + '! videoconvert name=inference_videoconvert n-threads=2 '
        + QUEUE("inference_hailonet_q", leaky="no", max_size_buffers=3)
        + f'! hailonet name=inference_hailonet hef-path={self.hef_path} batch-size={self.batch_size} vdevice-group-id=1 {self.thresholds_str} force-writable=true '
        + QUEUE("inference_hailofilter_q", leaky="no", max_size_buffers=3)
        + f'! hailofilter name=inference_hailofilter so-path={self.default_postprocess_so} {self.labels_config} qos=false '
        + QUEUE("inference_output_q", leaky="no", max_size_buffers=3)
        + '! inference_wrapper_agg.sink_1 '
        + 'inference_wrapper_agg. '
        + QUEUE("inference_wrapper_output_q", leaky="no", max_size_buffers=3)
        + '! hailotracker name=hailo_tracker class-id=1 kalman-dist-thr=0.8 iou-thr=0.9 init-iou-thr=0.7 keep-new-frames=2 keep-tracked-frames=15 keep-lost-frames=2 keep-past-metadata=False qos=False '
        + QUEUE("hailo_tracker_q", leaky="no", max_size_buffers=3)
        + QUEUE("hailo_display_overlay_q", leaky="no", max_size_buffers=3)
        + '! hailooverlay name=hailo_display_overlay '
        + QUEUE("identity_callback_q", leaky="no", max_size_buffers=3)
        + '! identity name=identity_callback '
        + QUEUE("hailo_display_videoconvert_q", leaky="no", max_size_buffers=3)
        + '! videoconvert name=hailo_display_videoconvert n-threads=2 qos=false '
        + QUEUE("queue_textoverlay_top")
        + '! textoverlay name=hailo_text_top text="" valignment=top halignment=center '
        + QUEUE("queue_textoverlay_bottom")
        + '! textoverlay name=hailo_text_bottom text="" valignment=bottom halignment=center '
        + QUEUE("hailo_display_q", leaky="no", max_size_buffers=3)
        + f'! fpsdisplaysink name=hailo_display video-sink={self.video_sink} sync={self.sync} text-overlay={self.options_menu.show_fps} signal-fps-measurements=true'
    )
    
    print("✅ Pipeline RTSP COMPLETO configurado (compatible con detection.py)")
    print(f"🎯 Usando: rtspsrc location='{self.rtsp_url}'")
    
    return complete_rtsp_pipeline

# -----------------------------------------------------------------------------------------------
# User Gstreamer Application
# -----------------------------------------------------------------------------------------------
# This class inherits from the hailo_rpi_common.GStreamerApp class
class GStreamerDetectionApp(GStreamerApp):
  def __init__(self, args, user_data):
    # Call the parent class constructor
    super().__init__(args, user_data)
    # Additional initialization code can be added here
    # Set Hailo parameters these parameters should be set based on the model used
    self.batch_size = 1
    self.network_width = 640
    self.network_height = 640
    self.network_format = "RGB"
    nms_score_threshold = 0.3
    nms_iou_threshold = 0.45
        # Temporary code: new postprocess will be merged to TAPPAS.
    # Check if new postprocess so file exists
    new_postprocess_path = os.path.join(self.current_path, '../resources/libyolo_hailortpp_post.so')
    if os.path.exists(new_postprocess_path):
      self.default_postprocess_so = new_postprocess_path
    else:
      self.default_postprocess_so = os.path.join(self.postprocess_dir, 'libyolo_hailortpp_post.so')
    if args.hef_path is not None:
      self.hef_path = args.hef_path
    # Set the HEF file path based on the network
    elif args.network == "yolov6n":
      self.hef_path = os.path.join(self.current_path, '../resources/yolov6n.hef')
    elif args.network == "yolov8s":
      self.hef_path = os.path.join(self.current_path, '../resources/yolov8s_h8l.hef')
    elif args.network == "yolox_s_leaky":
      self.hef_path = os.path.join(self.current_path, '../resources/yolox_s_leaky_h8l_mz.hef')
    else:
      assert False, "Invalid network type"
    # User-defined label JSON file
    if args.labels_json is not None:
      self.labels_config = f' config-path={args.labels_json} '
      # Temporary code
      if not os.path.exists(new_postprocess_path):
        print("New postprocess so file is missing. It is required to support custom labels. Check documentation for more information.")
        exit(1)
    else:
      self.labels_config = ''
    self.app_callback = app_callback
    self.thresholds_str = (
      f"nms-score-threshold={nms_score_threshold} "
      f"nms-iou-threshold={nms_iou_threshold} "
      f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
    )
    # Set the process title
    setproctitle.setproctitle("booth visitor counter")
    self.create_pipeline()
  def get_pipeline_string(self):
    if self.source_type == "rpi":
      source_element = (
        #"libcamerasrc name=src_0 auto-focus-mode=AfModeManual ! "
        "libcamerasrc name=src_0 auto-focus-mode=2 ! "
        f"video/x-raw, format={self.network_format}, width=1536, height=864 ! "
        + QUEUE("queue_src_scale")
        + "videoscale ! "
        f"video/x-raw, format={self.network_format}, width={self.network_width}, height={self.network_height}, framerate=60/1 ! "
        #f"video/x-raw, format={self.network_format}, width={self.network_width}, height={self.network_height} ! "
      )
    elif self.source_type == "usb":
      source_element = (
        f"v4l2src device={self.video_source} name=src_0 ! "
        "video/x-raw, width=640, height=480, framerate=30/1 ! "
      )
    else:
      source_element = (
        f"filesrc location={self.video_source} name=src_0 ! "
        + QUEUE("queue_dec264")
        + " qtdemux ! h264parse ! avdec_h264 max-threads=2 ! "
        " video/x-raw, format=I420 ! "
      )
    source_element += QUEUE("queue_scale")
    source_element += "videoscale n-threads=2 ! "
    source_element += QUEUE("queue_src_convert")
    source_element += "videoconvert n-threads=3 name=src_convert qos=false ! "
    source_element += f"video/x-raw, format={self.network_format}, width={self.network_width}, height={self.network_height}, pixel-aspect-ratio=1/1 ! "
    pipeline_string = (
      "hailomuxer name=hmux "
      + source_element
      + "tee name=t ! "
      + QUEUE("bypass_queue", max_size_buffers=20)
      + "hmux.sink_0 "
      + "t. ! "
      + QUEUE("queue_hailonet")
      + "videoconvert n-threads=3 ! "
      f"hailonet hef-path={self.hef_path} batch-size={self.batch_size} {self.thresholds_str} force-writable=true ! "
      + QUEUE("queue_hailofilter")
      + f"hailofilter so-path={self.default_postprocess_so} {self.labels_config} qos=false ! "
      + QUEUE("queue_hailotracker")
      + "hailotracker keep-tracked-frames=3 keep-new-frames=3 keep-lost-frames=3 ! "
      + QUEUE("queue_hmuc")
      + "hmux.sink_1 "
      + "hmux. ! "
      + QUEUE("queue_hailo_python")
      + QUEUE("queue_user_callback")
      + "identity name=identity_callback ! "
      + QUEUE("queue_hailooverlay")
      + "hailooverlay ! "
      + QUEUE("queue_videoconvert")
      + "videoconvert n-threads=3 qos=false ! "
      + QUEUE("queue_textoverlay_top")
      + "textoverlay name=hailo_text_top text='' valignment=top halignment=center ! "
      + QUEUE("queue_textoverlay_bottom")
      + "textoverlay name=hailo_text_bottom text='' valignment=bottom halignment=center ! "
      + QUEUE("queue_hailo_display")
      + f"fpsdisplaysink video-sink={self.video_sink} name=hailo_display sync={self.sync} text-overlay={self.options_menu.show_fps} signal-fps-measurements=true "
    )
    print(pipeline_string)
    return pipeline_string
if __name__ == "__main__":
  # Create an instance of the user app callback class
  user_data = user_app_callback_class()
  START = sv.Point(340, 0)
  END = sv.Point(340, 640)
  line_zone = sv.LineZone(start=START, end=END, triggering_anchors=(sv.Position.CENTER,sv.Position.TOP_CENTER, sv.Position.BOTTOM_CENTER))
  parser = get_default_parser()
  # Add additional arguments here
  parser.add_argument(
    "--network",
    default="yolov6n",
    choices=['yolov6n', 'yolov8s', 'yolox_s_leaky'],
    help="Which Network to use, default is yolov6n",
  )
  parser.add_argument(
    "--hef-path",
    default=None,
    help="Path to HEF file",
  )
  parser.add_argument(
    "--labels-json",
    default=None,
    help="Path to costume labels JSON file",
  )
  parser.add_argument(
    "--rtsp-url",
    default=None,
    help="RTSP URL for camera stream",
  )
  args = parser.parse_args()
  
  # Use RTSP app if rtsp_url is provided, otherwise use standard app
  if args.rtsp_url:
    print(f"🎥 Usando RTSP: {args.rtsp_url}")
    app = RTSPGStreamerDetectionApp(args, user_data, args.rtsp_url)
  else:
    print("📹 Usando fuente estándar (rpi/usb/archivo)")
    app = GStreamerDetectionApp(args, user_data)
  
  app.run()