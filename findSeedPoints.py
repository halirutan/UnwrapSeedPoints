from dataclasses import dataclass

import numpy as np
import nibabel as nib
from scipy import ndimage
from simple_parsing import ArgumentParser
from skimage import morphology
from scipy.ndimage import distance_transform_cdt, generic_filter
import logging
import os
import re

logging.basicConfig()
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


def phase_jumps_by_generic_filter(data: np.ndarray) -> np.ndarray:
    filtered = generic_filter(
        data,
        lambda x: np.int32(np.max(x) > 0.9 * np.pi and np.min(x) < -0.9 * np.pi),
        footprint=np.ones((2, 2, 2)),
        mode="constant",
        cval=-np.pi
    )
    return 1 - np.int32(np.logical_or(filtered, data == 0.0))


def phase_jumps_by_correlation(data: np.ndarray) -> np.ndarray:
    logger.info("Calculate phase jumps by correlation")
    kernel = [[[0, -1, 0], [-1, 0, 1], [0, 1, 0]]]
    filtered = np.abs(ndimage.correlate(data, weights=kernel))
    threshold = np.quantile(filtered, 0.9)
    return 1 - np.int32(np.logical_or(filtered > threshold, data == 0.0))


def seed_points_by_distance_transform(data: np.ndarray, num_seed_points: int) -> tuple[
    np.ndarray, np.ndarray, np.ndarray]:
    logger.info("Calculate distance transform")
    distance_transform = distance_transform_cdt(data)
    logger.info("Calculate seed points")
    threshold = np.quantile(distance_transform, 0.99)
    seed_indices = np.transpose(np.where(distance_transform > threshold))
    rng = np.random.default_rng()
    logger.info(f"Selecting {num_seed_points} seeds")
    indices_selection = rng.choice(seed_indices, min(num_seed_points, len(seed_indices)))
    index_image = np.zeros_like(data)
    index_image.ravel()[np.ravel_multi_index(indices_selection.T, data.shape)] = 1
    return distance_transform, index_image, indices_selection


@dataclass
class CmdOptions:
    """
    Provides a method to calculate seed points for phase-unwrapping from phase images.
    """
    input: str
    """Input phase map Nifti file"""
    output_dir: str
    """Output directory files"""
    n: int
    """Number of seed points to create"""


def main():
    logger.setLevel(logging.INFO)
    parser = ArgumentParser()
    # noinspection PyTypeChecker
    parser.add_arguments(CmdOptions, dest="options")
    args = parser.parse_args()
    cmd_options: CmdOptions = args.options

    nifti_file = cmd_options.input
    if not os.path.isfile(nifti_file) or not nifti_file.endswith((".nii", ".nii.gz")):
        logger.error("Input file must be a nifti file")
        exit(1)

    output_dir = cmd_options.output_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    num_seed_points = cmd_options.n
    if num_seed_points <= 0:
        logger.error("Number of seed points must be a positive integer")
        exit(1)

    img = load_nifti(nifti_file)
    phase_jumps = phase_jumps_by_correlation(img.get_fdata())
    distance_transform, seed_points_image, seed_points_coordinates = seed_points_by_distance_transform(
        phase_jumps, num_seed_points)
    # Increase the size of the seed points in the image for better visibility
    logger.info("Increasing the size of seed points in the image for better visualization")
    seed_points_image = morphology.dilation(seed_points_image, footprint=morphology.ball(3))
    logger.info("Saving distance transform image")
    nib.save(nib.Nifti1Image(
        distance_transform,
        img.affine,
        img.header),
        os.path.join(output_dir, "distance_transform.nii"))
    logger.info("Saving seed points image")
    nib.save(nib.Nifti1Image(
        seed_points_image,
        img.affine,
        img.header),
        os.path.join(output_dir, "seed_points.nii"))

    logger.info("Saving thresholded distance transform image")
    thresh = np.quantile(distance_transform, 0.99)
    nib.save(nib.Nifti1Image(
        np.int32(distance_transform > thresh),
        img.affine,
        img.header),
        os.path.join("distance_transform_threshold.nii"))

    logger.info("Saving seed point coordinates")
    np.savetxt(os.path.join(output_dir, "seed_points_coordinates.txt"), seed_points_coordinates, fmt="%d")


if __name__ == '__main__':
    main()
