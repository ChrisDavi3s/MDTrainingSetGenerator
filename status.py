import os
import argparse
import re

def get_valid_cif_files(directory):
    """
    Finds valid CIF files in the given directory and its subdirectories.
    A CIF file is considered valid if it does not contain "_dont_use" in its name.
    
    Args:
        directory (str): The directory to search for valid CIF files.
    
    Returns:
        set: A set containing the base names (without the extension) of the valid CIF files.
    """
    valid_cif_files = set()
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".cif") and "_dont_use" not in file:
                valid_cif_files.add(os.path.splitext(file)[0])
    return valid_cif_files

def get_job_status(directory, iteration):
    """
    Determines the status of a job based on the presence of the REPORT file.
    
    Args:
        directory (str): The directory to check for the REPORT file.
        iteration (int): The iteration number.
    
    Returns:
        str: The status of the job ("completed" or "not_started").
    """
    report_file = os.path.join(directory, f"{iteration:02d}_aimd_REPORT")

    if os.path.isfile(report_file):
        return "completed"
    else:
        return "not_started"

def analyze_calculations(directory, valid_cif_files):
    """
    Analyzes the calculations in the given directory and its subdirectories.
    Only considers directories where the base name corresponds to a valid CIF file.
    
    Args:
        directory (str): The directory to analyze the calculations.
        valid_cif_files (set): A set containing the base names of the valid CIF files.
    
    Returns:
        dict: A nested dictionary containing the analyzed calculations.
    """
    calculations = {}
    for root, dirs, files in os.walk(directory):
        if "POSCAR" in files:
            path_parts = root.split(os.sep)
            if len(path_parts) >= 6:
                base_name = path_parts[-5]
                functional = path_parts[-4]
                ensemble = path_parts[-3]
                scaling = path_parts[-2]
                temperature = int(path_parts[-1])

                if base_name not in valid_cif_files:
                    continue

                if functional not in calculations:
                    calculations[functional] = {}
                if base_name not in calculations[functional]:
                    calculations[functional][base_name] = {}
                if temperature not in calculations[functional][base_name]:
                    calculations[functional][base_name][temperature] = {"npt": {"completed": 0, "not_started": 0},
                                                                        "nvt": {"completed": 0, "not_started": 0}}

                iterations = sorted(set(int(file[:2]) for file in files if re.match(r'^\d{2}_aimd_', file)))
                for iteration in iterations:
                    job_status = get_job_status(root, iteration)
                    calculations[functional][base_name][temperature][ensemble][job_status] += 1

    return calculations

def print_summary(calculations):
    """
    Prints a summary of the analyzed calculations in a compact format.
    
    Args:
        calculations (dict): A nested dictionary containing the analyzed calculations.
    """
    for functional, structures in calculations.items():
        print(f"Functional: {functional}\n")
        print("{:<25} {:<12} {:<4} {:<4} {:<6} {:<6}".format(
            "Structure", "Temperature", "npt", "nvt", "npt(q)", "nvt(q)"))
        print("-" * 80)
        for structure, temperatures in structures.items():
            temperatures_sorted = sorted(temperatures.items(), key=lambda x: x[0])
            for i, (temperature, status_counts) in enumerate(temperatures_sorted):
                npt_completed = status_counts["npt"]["completed"]
                npt_not_started = status_counts["npt"]["not_started"]
                nvt_completed = status_counts["nvt"]["completed"]
                nvt_not_started = status_counts["nvt"]["not_started"]
                if i == 0:
                    print("{:<25} {:<12} {:<4} {:<4} {:<6} {:<6}".format(
                        structure, temperature, npt_completed, nvt_completed, npt_not_started, nvt_not_started))
                else:
                    print("{:<25} {:<12} {:<4} {:<4} {:<6} {:<6}".format(
                        "", temperature, npt_completed, nvt_completed, npt_not_started, nvt_not_started))
            print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze calculations.")
    parser.add_argument("directory", type=str, help="Path to the top-level directory containing calculations.")
    args = parser.parse_args()

    valid_cif_files = get_valid_cif_files(args.directory)
    calculations = analyze_calculations(args.directory, valid_cif_files)
    print_summary(calculations)
