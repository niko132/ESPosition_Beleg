from PIL import Image

ENVIRONMENTS = {
    "flat": ("flat.png", 8.19),
    "apb": ("apb.png", 10.0),
    "apb_3081_scaled": ("apb_3081_scaled_fingerprints.png", 21.52),
    "flat_scaled": ("flat_scaled_fingerprints.png", 8.19)
}

CURRENT_ENV = "flat_scaled"

#PATH_LOSS_L0 = -45.0 # -45.0
#PATH_LOSS_EXP = 4.5 # 3.0
PATH_LOSS_L0 = -50.0 # -45.0
PATH_LOSS_EXP = 3.5 # 3.0

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

def get_scaled_env_background_image():
    background = get_env_background_image()
    # scale so that 1px = 1cm
    new_size = (int(background.size[0] * env_to_m(100)), int(background.size[1] * env_to_m(100)))
    return background.resize(new_size, Image.LANCZOS)