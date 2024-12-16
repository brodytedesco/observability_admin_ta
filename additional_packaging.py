from os.path import dirname, realpath, join, exists, isfile
from os import makedirs, listdir
from shutil import copy2

def additional_packaging(ta_name: str):
    """
    Copy all files from the configurations directory into output/{ta_name}/default.
    """
    if not ta_name:
        raise ValueError("ta_name must be provided to additional_packaging.")

    try:
        base_dir = dirname(realpath(__file__))
        source_dir = join(base_dir, "configurations")
        target_dir = join(base_dir, "output", ta_name, "default")

        # Iterate over all files in configurations directory
        for filename in listdir(source_dir):
            source_file = join(source_dir, filename)
            
            # Only copy regular files, not directories
            if isfile(source_file):
                copy2(source_file, target_dir)
    except Exception as e:
        raise IOError(f"Failed to copy {source_file} to {target_dir}: {e}") from e

    try:
        base_dir = dirname(realpath(__file__))
        source_dir = join(base_dir, "dashboards")
        target_dir = join(base_dir, "output", ta_name, "default", "data","ui", "views")

        # Ensure the target directory exists
        if not exists(target_dir):
            makedirs(target_dir)

        # Iterate over all files in the dashboards directory
        for filename in listdir(source_dir):
            source_file = join(source_dir, filename)

            # Only copy regular files, not directories
            if isfile(source_file):
                copy2(source_file, target_dir)
    except Exception as e:
    # If there's an error copying, raise a new exception with the original error message
        raise IOError(f"Failed to copy {source_file} to {target_dir}: {e}") from e
    
    try:
        base_dir = dirname(realpath(__file__))
        source_dir = join(base_dir, "navigator")
        target_dir = join(base_dir, "output", ta_name, "default", "data","ui", "nav")

        # Ensure the target directory exists
        if not exists(target_dir):
            makedirs(target_dir)

        # Iterate over all files in the dashboards directory
        for filename in listdir(source_dir):
            source_file = join(source_dir, filename)

            # Only copy regular files, not directories
            if isfile(source_file):
                copy2(source_file, target_dir)

    except Exception as e:
    # If there's an error copying, raise a new exception with the original error message
        raise IOError(f"Failed to copy {source_file} to {target_dir}: {e}") from e
    
    try:
        base_dir = dirname(realpath(__file__))
        source_dir = join(base_dir, "static")
        target_dir = join(base_dir, "output", ta_name, "static")

        # Ensure the target directory exists
        if not exists(target_dir):
            makedirs(target_dir)

        # Iterate over all files in the dashboards directory
        for filename in listdir(source_dir):
            source_file = join(source_dir, filename)

            # Only copy regular files, not directories
            if isfile(source_file):
                copy2(source_file, target_dir)
    except Exception as e:
    # If there's an error copying, raise a new exception with the original error message
        raise IOError(f"Failed to copy {source_file} to {target_dir}: {e}") from e
    
        


def cleanup_output_files(output_path: str, ta_name: str) -> None:
    """
    prepare a list for the files to be deleted after the source code has been copied to output directory
    :param output_path: The path provided in --output argument in ucc-gen command or the default output path.
    :param ta_name: The add-on name which is passed as a part of --addon-name argument during ucc-gen init 
                    or present in app.manifest file of add-on.
    """
    # files_to_delete = []
    # files_to_delete.append(sep.join([output_path, ta_name, "default", "redundant.conf"]))
    # files_to_delete.append(sep.join([output_path, ta_name, "bin", "template_modinput_layout.py"]))
    # files_to_delete.append(sep.join([output_path, ta_name, "bin", "example_one_input_one.py"]))
    # files_to_delete.append(sep.join([output_path, ta_name, "bin", "template_rest_handler_script.py"]))
    # files_to_delete.append(sep.join([output_path, ta_name, "bin", "file_does_not_exist.py"]))
    # files_to_delete.append(sep.join([output_path, ta_name, "default", "nav", "views", "file_copied_from_source_code.xml"]))

    # for delete_file in files_to_delete:
    #     try:
    #         remove(delete_file)
    #     except (FileNotFoundError):
    #         # simply pass if the file doesn't exist
    #         pass