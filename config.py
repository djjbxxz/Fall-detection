def get_default_config():
    DEBUG=False
    return locals()

def get_openpose_config():
    model_folder = "/openpose/models/"
    model_pose = "BODY_25"
    net_resolution = "400x320"
    render_threshold = 0.30
    return locals()
