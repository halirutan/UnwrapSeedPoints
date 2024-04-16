import math

import numpy as np
import nibabel as nib
from skimage import morphology
import logging
import os
import re

logger = logging.getLogger(__name__)


def load_nifti(filename: str) -> nib.Nifti1Image:
    _, ext = os.path.splitext(filename)
    if os.path.isfile(filename) and re.match("\\.nii(\\.gz)?", ext):
        img = nib.load(filename)
        if isinstance(img, nib.Nifti1Image):
            return img
        else:
            logger.error("Nifti image not loaded because it is not a nifti1 image")
    else:
        logger.error(f"Could not load nifti file '{filename}'")
    exit(1)


def interval_component_labeling(data: np.ndarray) -> np.ndarray:
    # split data into equal intervals
    ranges = [
        (-math.pi / 3.0, 0.0),
        (0.0, math.pi / 3.0),
        (-math.pi, -2.0 * math.pi / 3.0),
        (-2.0 * math.pi / 3.0, -math.pi / 3.0),
        (math.pi / 3.0, 2.0 * math.pi / 3.0),
        (2.0 * math.pi / 3.0, math.pi)
    ]
    # ranges = [(- 2.0 * math.pi / 3.0, -0.1), (0.1, 2.0 * math.pi / 3.0)]
    # ranges = [(-1, 0)]
    output_label_image = np.zeros_like(data, dtype=np.int32)
    for iter_num, (start, end) in enumerate(ranges):
        # component labeling for each interval
        mask = np.logical_and(data > start, data < end)
        mask = morphology.closing(mask, footprint=morphology.ball(2))

        if iter_num < 2:
            labeled_array, num_features = morphology.label(mask, return_num=True)
            label_count = np.bincount(labeled_array.ravel())
            label_count[0] = 0
            largest_label = label_count.argmax()
            largest_label_image = np.zeros_like(data, dtype=np.int32)
            largest_label_image[labeled_array == largest_label] = iter_num
            output_label_image += largest_label_image
        else:
            output_label_image[mask] = 0
        # throw out small components
    return output_label_image

    # patch everything together
