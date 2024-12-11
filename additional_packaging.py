from os.path import sep, exists, dirname, realpath, join
from os import makedirs
from shutil import copy2

def additional_packaging(ta_name: str):
    """
    Copy props.conf from configurations directory into output/{ta_name}/default.
    """
    # Ensure ta_name is provided
    if not ta_name:
        raise ValueError("ta_name must be provided to additional_packaging.")

    # Define the source and target paths
    base_dir = dirname(realpath(__file__))
    source_file = join(base_dir, "configurations", "props.conf")
    target_dir = join(base_dir, "output", ta_name, "default")

    # Make sure the target directory exists
    if not exists(target_dir):
        makedirs(target_dir)

    # Copy the file
    if exists(source_file):
        copy2(source_file, target_dir)
    else:
        raise FileNotFoundError(f"Source file does not exist: {source_file}")

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