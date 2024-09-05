from PIL import Image

ENVIRONMENTS = {
    "flat": ("flat.png", 8.19)
}

CURRENT_ENV = "flat"

PATH_LOSS_L0 = -45.0 # -45.0
PATH_LOSS_EXP = 4.5 # 3.0

def get_env_background_filename():
    (filename, _) = ENVIRONMENTS[CURRENT_ENV]
    return filename
    
def get_env_background_image():
    return Image.open(get_env_background_filename())

def env_to_px(dim_in_m):
    (_, width_in_m) = ENVIRONMENTS[CURRENT_ENV]
    background = get_env_background_image()
    (width_in_px, _) = background.size
    return width_in_px / width_in_m * dim_in_m

def env_to_m(dim_in_px):
    (_, width_in_m) = ENVIRONMENTS[CURRENT_ENV]
    background = get_env_background_image()
    (width_in_px, _) = background.size
    return width_in_m / width_in_px * dim_in_px