import os, re
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import time
from tqdm import tqdm

default_log_path = '/home/radu/Documents/Connection/renaming_log'

""" 
Save the rename action to a log file
"""
def log_rename_action(old_name, new_name, log_path = default_log_path):

    # If the log file does not exist, create it and write the first line
    if not os.path.exists(log_path):
        with open(log_path, 'w') as log_file:
            log_file.write(f'{time.ctime(int(time.time()))} - Log file created\n')

    # Write the renaming action to the log file
    with open(log_path, 'a') as log_file:
        log_file.write(f'[{time.ctime(int(time.time()))}] Renamed "{old_name}" to "{new_name}"\n')

""" 
Check whether image directory is valid
"""
def valid_image_directory(folder_name):

    return re.match(r'^\d{4}-\d{2}-\d{2} - ', folder_name)

""" 
Obtain the day when image was taken, from EXIF data
"""
def get_exif_date(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        print(f"Error reading EXIF from {image_path}: {e}")
    return None

""" 
Obtain the day when video was taken, from EXIF data
"""
def get_video_creation_date(video_path):
    try:
        parser = createParser(video_path)
        metadata = extractMetadata(parser)
        if metadata and metadata.has("creation_date"):
            return metadata.get("creation_date").replace(tzinfo=None)
    except Exception as e:
        print(f"Error reading metadata from {video_path}: {e}")
    return None

""" 
Obtain day when file was last modified
"""
def get_file_modification_date(file_path):
    timestamp = os.path.getmtime(file_path)
    return datetime.fromtimestamp(timestamp)

""" 
Rename a single image or video file
"""
def single_file_rename(filename, filetype, 
                       current_parent_directory, new_parent_directory, author_name,
                       def_tag = 'ACN_', def_error_tag = 'ACNE_'):

    # Construct current full path
    current_full_path = os.path.join(current_parent_directory, filename)

    # Check that the file exists
    if not os.path.exists(current_full_path):
        print(f"File {current_full_path} does not exist!")
        return

    # Fork based on filetype
    if filetype == 'image':

        # Try to get the EXIF date; if successful, leading tag is default
        file_date = get_exif_date(current_full_path)
        crt_tag = def_tag

    elif filetype == 'video':

        # Try to get the video creation date; if successful, leading tag is default
        file_date = get_video_creation_date(current_full_path)
        crt_tag = def_tag
    
    # If the date was successfully obtained, check that year is not before 2000
    if file_date:
        if file_date.year < 2000: file_date = None

    # Fallback to file modification date, leading tag is error
    if not file_date:
        file_date = get_file_modification_date(current_full_path)
        crt_tag = def_error_tag

    # Format new filename
    new_filename = crt_tag + file_date.strftime('%Y_%m_%d_%H_%M_%S') + f'_{author_name}' + os.path.splitext(filename)[1]
    new_full_path = os.path.join(new_parent_directory, new_filename)

    # Handle filename conflicts
    counter = 1
    while os.path.exists(new_full_path):
        new_filename = crt_tag + file_date.strftime('%Y_%m_%d_%H_%M_%S') + f'_{author_name}' + f'_{counter}' + os.path.splitext(filename)[1]
        new_full_path = os.path.join(new_parent_directory, new_filename)
        counter += 1

    # Rename the file
    os.rename(current_full_path, new_full_path)
    log_rename_action(current_full_path, new_full_path)

""" 
Manage a full event folder
"""
def manage_event_folder(folder_name, crt_parent_path, new_parent_path, author_name, show_progress = False):

    # Construct full paths
    current_folder_path = os.path.join(crt_parent_path, folder_name)
    new_folder_path = os.path.join(new_parent_path, folder_name)

    # Check that the folder exists
    if not os.path.exists(current_folder_path):
        print(f"Folder {current_folder_path} does not exist!")
        return

    # Create new folder if it does not exist
    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)

    # If show_progress is True, use tqdm to show progress
    if show_progress: 
        dir_iter = tqdm(os.listdir(current_folder_path))
    else:
        dir_iter = os.listdir(current_folder_path)

    # Iterate through files in the folder, deal with them
    for filename in dir_iter:

        # Check whether it is an acceptable image
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.webp')):

            # Rename the file
            single_file_rename(filename = filename, filetype = 'image', current_parent_directory = current_folder_path, 
                               new_parent_directory = new_folder_path, author_name = author_name)
            
        # Check whether it is an acceptable video
        if filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):

            # Rename the file
            single_file_rename(filename = filename, filetype = 'video', current_parent_directory = current_folder_path, 
                               new_parent_directory = new_folder_path, author_name = author_name)
    
""" 
Manage all content of an author folder
"""        
def manage_author_content(author_name, author_parent_directory, archive_directory, show_progress = False):

    # Construct full paths
    current_author_path = os.path.join(author_parent_directory, author_name)

    # Check that the folder exists
    if not os.path.exists(current_author_path):
        print(f"Author folder {current_author_path} does not exist!")
        return

    # Iterate through folders in the author folder, deal with them
    for folder_name in os.listdir(current_author_path):
        
        # Check that the folder name is valid
        if not valid_image_directory(folder_name):
            continue

        # If it matches, call the manage_event_folder function
        manage_event_folder(folder_name = folder_name, crt_parent_path = current_author_path, 
                            new_parent_path = archive_directory, author_name = author_name, show_progress = show_progress)
        
        # After managing the folder, check whether it is empty; if so, remove it
        if not os.listdir(os.path.join(current_author_path, folder_name)):
            os.rmdir(os.path.join(current_author_path, folder_name))

"""
Separate method to clear empty folders
"""
def clear_empty_folders(author_name, author_parent_directory):

    # Construct full paths
    current_author_path = os.path.join(author_parent_directory, author_name)

    # Check that the folder exists
    if not os.path.exists(current_author_path):
        print(f"Author folder {current_author_path} does not exist!")
        return

    # Iterate through folders in the author folder, deal with them
    for folder_name in os.listdir(current_author_path):
        
        # Check that the folder name is valid
        if not valid_image_directory(folder_name):
            continue

        # Construct full path
        folder_path = os.path.join(current_author_path, folder_name)

        # Check if the folder is empty
        if not os.path.exists(folder_path):
            print(f"Folder {folder_path} does not exist!")
            continue

        # Check if the folder is empty
        if not os.listdir(folder_path):
            print(f"Folder {folder_path} is empty, deleting...")
            os.rmdir(folder_path)
            continue

""" 
Fix pre-2000 file names; single file
"""
def fix_single_filename(filename, current_full_path, new_parent_directory, author_name, def_error_tag = 'ACNE_'):

    file_date = get_file_modification_date(current_full_path)
    crt_tag = def_error_tag

    # Format new filename
    new_filename = crt_tag + file_date.strftime('%Y_%m_%d_%H_%M_%S') + f'_{author_name}' + os.path.splitext(filename)[1]
    new_full_path = os.path.join(new_parent_directory, new_filename)

    # Handle filename conflicts
    counter = 1
    while os.path.exists(new_full_path):
        new_filename = crt_tag + file_date.strftime('%Y_%m_%d_%H_%M_%S') + f'_{author_name}' + f'_{counter}' + os.path.splitext(filename)[1]
        new_full_path = os.path.join(new_parent_directory, new_filename)
        counter += 1

    # Rename the file
    os.rename(current_full_path, new_full_path)
    log_rename_action(current_full_path, new_full_path)

""" 
Fix pre-2000 file names; single directory
"""
def fix_past_names_single_dir(dir_path, name_tags = ['ACN_', 'ACNE_']):

    # Take all files in directory which contain any of the name tags
    candidate_files = [f for f in os.listdir(dir_path) if any(tag in f for tag in name_tags)]

    # Loop over files
    for filename in candidate_files:

        # The format is TAG_YYYY_MM_DD_ and so on. Extract year from each file
        year = int(filename.split('_')[1])

        # If the year is less than 2000, try to fix it
        if year < 2000:

            # Extract author name from filename; this is last unless followed by a number
            author_name = filename.split('_')[-1].split('.')[0]

            # Catch the case where the author name is followed by a number, which could be a multi-digit counter
            if author_name.isdigit():
                author_name = filename.split('_')[-2]

            # Fix the filename
            fix_single_filename(filename = filename, 
                                current_full_path = os.path.join(dir_path, filename), 
                                new_parent_directory = dir_path, author_name = author_name)

""" 
Fix pre-2000 file names; all valid directories
"""
def fix_path_names_all_dir(dir_path):

    # Iterate through folders in the author folder, deal with them
    for folder_name in os.listdir(dir_path):
        
        # Check that the folder name is valid
        if not valid_image_directory(folder_name):
            continue

        # Get the full path of the folder
        folder_path = os.path.join(dir_path, folder_name)

        # Fix the filenames in the folder
        fix_past_names_single_dir(folder_path)






