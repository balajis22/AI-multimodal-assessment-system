# -----------------------------------------------------------------------------
# Linux & Cloud Environment Preparation
# MUST be set and imported before any TensorFlow, MediaPipe, or OpenCV modules
# to avoid LLVM command-line symbol conflicts ("Option registered more than once")
# -----------------------------------------------------------------------------
import os

# Suppress verbose TensorFlow/CUDA warnings and avoid GPU lookup on headless cloud
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Pre-import PyTorch to register LLVM cleanly before TensorFlow initializes
try:
    import torch  # noqa: F401
except ImportError:
    pass

# Launch the main frontend application
from frontend.app import *  # noqa: F401,F403
