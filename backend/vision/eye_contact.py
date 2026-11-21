from backend.vision.face_detector import get_face_mesh_detector


def detect_eye_contact(frame):
    """
    Detect eye contact direction.

    Returns:
        direction (str)
    """
    detector = get_face_mesh_detector()
    img, faces = detector.findFaceMesh(frame, draw=False)

    if not faces:
        return "No Face"

    face = faces[0]

    # Iris centers
    left_iris = face[468]
    right_iris = face[473]

    # Eye corners
    left_eye_left = face[33]
    left_eye_right = face[133]

    right_eye_left = face[362]
    right_eye_right = face[263]

    # Horizontal ratios
    left_ratio = (
        (left_iris[0] - left_eye_left[0]) /
        (left_eye_right[0] - left_eye_left[0] + 1e-6)
    )

    right_ratio = (
        (right_iris[0] - right_eye_left[0]) /
        (right_eye_right[0] - right_eye_left[0] + 1e-6)
    )

    ratio = (left_ratio + right_ratio) / 2

    if ratio < 0.35:
        direction = "Looking Right"

    elif ratio > 0.65:
        direction = "Looking Left"

    else:
        direction = "Looking Center"

    return direction
