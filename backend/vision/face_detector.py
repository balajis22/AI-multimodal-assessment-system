# --------------------------------------------------
# Shared Lazy FaceMesh Detector Singleton
# Avoids initializing MediaPipe / XNNPACK multiple times
# --------------------------------------------------

_detector = None


def get_face_mesh_detector():
    global _detector
    if _detector is None:
        from cvzone.FaceMeshModule import FaceMeshDetector
        _detector = FaceMeshDetector(maxFaces=1)
    return _detector
