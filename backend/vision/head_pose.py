import numpy as np

from backend.vision.face_detector import get_face_mesh_detector


def detect_head_pose(frame):
    """
    Detect head pose direction.

    Returns:
        direction (str)
    """
    detector = get_face_mesh_detector()
    img, faces = detector.findFaceMesh(frame, draw=False)

    if not faces:
        return "No Face"

    face = faces[0]

    # Nose tip
    nose = np.array(face[1])

    # Left & right cheeks
    left = np.array(face[234])
    right = np.array(face[454])

    # Forehead & chin
    forehead = np.array(face[10])
    chin = np.array(face[152])

    # Face center
    center = (left + right) / 2

    horizontal = nose[0] - center[0]
    vertical = nose[1] - ((forehead[1] + chin[1]) / 2)

    if horizontal < -15:
        direction = "Looking Right"

    elif horizontal > 15:
        direction = "Looking Left"

    elif vertical < -10:
        direction = "Looking Up"

    elif vertical > 15:
        direction = "Looking Down"

    else:
        direction = "Center"

    return direction
