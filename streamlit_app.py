import os

# Suppress verbose TensorFlow/CUDA warnings and avoid GPU lookup on headless cloud
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Launch the main frontend application
from frontend.app import *  # noqa: F401,F403
