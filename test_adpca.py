import os
import re
import shutil
from findSeedPoints import find_seed_points

root_dir = "/Users/pscheibe/mnt"
subjects = [
    "s001",
    "s002",
    "s003",
    "s004",
    "s005",
    "s006",
    "s007",
    "s008",
    "s009",
    "s010",
    "s011",
    "s012",
    "s013",
    "s014",
    "s015",
    "s016",
    "s017",
]

source_dir = os.path.join(root_dir, "0-source")
output_dir = os.path.join(root_dir, "2-tests", "20240423_test_unwrap_seed_points")
# output_dir = "/Users/pscheibe/PycharmProjects/UnwrapSeedPoints/out"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for subject in subjects:
    subject_dir = os.path.join(source_dir, subject, "FMRIB", "NIFTI_LORAKS")
    for mpm in ["MPM1", "MPM2"]:
        for contrast in ["PDw", "T1w"]:
            path = f"{subject_dir}/{mpm}/{contrast}"
            if os.path.isdir(path):
                pattern = re.compile(".*Echo_0[1,6]_Phase\\.nii")
                files = os.listdir(path)
                matched_files = [f for f in files if re.match(pattern, f)]
                for file in matched_files:
                    print(f"Processing {subject} {mpm} {contrast} {file[-12:-10]}")
                    subject_output_dir = f"{output_dir}/{subject}_{mpm}_{contrast}_{file[-12:-10]}"
                    os.makedirs(subject_output_dir, exist_ok=True)
                    find_seed_points(os.path.join(path, file), subject_output_dir, 20)
                    shutil.copyfile(os.path.join(path, file), os.path.join(subject_output_dir, "phase.nii"))
