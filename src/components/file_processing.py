import os
import re
import json
import shutil
from PIL import Image, ImageFile, UnidentifiedImageError
from io import BytesIO
import logging
from config.config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_empty_folder(folder_path):
    try:
        os.rmdir(folder_path)
    except OSError:
        pass

def create_temp_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
def initialize_dict(path_input, path_dict):
    if not path_dict or not os.path.exists(path_dict):
        path_dict = os.path.join(path_input, 'TEMP_FTS_dict.json')
        with open(path_dict, 'w', encoding='utf-8') as file:
            json.dump({}, file, ensure_ascii=False)
    return path_dict
        
def move_error(filename, path_input):
    path_title_in = os.path.join(path_input, filename)
    path_to_title_move = uniquify(os.path.join(path_input, 'TEMP_ERROR_IMAGES', filename))
    shutil.move(path_title_in, path_to_title_move)
    logger.error(f'Error: {filename}')

    
def move_images(title_name, filename, path_input, path_output, artist_name, character_name, img_web, is_sep_chars=False, is_dl_images=False, is_saucenao=False):
    path_title_in = os.path.join(path_input, filename)
    
    if character_name is not None:
        character_name = str(character_name).translate(str.maketrans(name_replacement))
        character_name = re.sub(r'\s+', ' ', character_name)
    if artist_name is not None:
        artist_name = str(artist_name).translate(str.maketrans(name_replacement))
        artist_name = re.sub(r'\s+', ' ', artist_name)

    if is_sep_chars:
        if title_name == 'Original' and artist_name is not None:
            path_title_out = os.path.join(path_output, title_name, artist_name).rstrip()
        elif title_name == 'Original' and artist_name is None:
            title_name = 'Unknown'
            path_title_out = os.path.join(path_output, title_name).rstrip()
        elif title_name == 'Original' and artist_name is not None and character_name is not None:
            path_title_out = os.path.join(path_output, title_name, artist_name, character_name).rstrip()
        elif title_name is not None and title_name != 'Original' and character_name is not None:
            path_title_out = os.path.join(path_output, title_name, character_name).rstrip()
        elif title_name is not None and title_name != 'Original' and character_name is None:
            path_title_out = os.path.join(path_output, title_name).rstrip()
        elif title_name is None:
            title_name = 'Unknown'
            path_title_out = os.path.join(path_output, title_name).rstrip()
    else:
        if title_name is None:
            title_name = 'Unknown'
            path_title_out = os.path.join(path_output, title_name).rstrip()
        else:
            path_title_out = os.path.join(path_output, title_name).rstrip()

    if not os.path.exists(path_title_out):
        os.makedirs(path_title_out)

    path_to_title_move = os.path.join(path_title_out, filename)
    rel_path = os.path.relpath(path_title_out, path_output).replace('\\', ' \ ')

    if os.path.exists(path_to_title_move):
        return [rel_path, path_title_in, path_to_title_move]
    else:
        shutil.move(path_title_in, path_to_title_move)
    return [rel_path, None, None]   
   

def move_unknown(filename, path_input, path_output):
    path_title_in = os.path.join(path_input, filename)
    path_title_out = os.path.join(path_output, 'Unknown').rstrip()
    path_to_title_move = os.path.join(path_title_out, filename)
    rel_path = os.path.relpath(path_title_out, path_output).replace('\\', ' \ ')

    if not os.path.exists(path_title_out):
        os.makedirs(path_title_out)

    if os.path.exists(path_to_title_move):
        return [rel_path, path_title_in, path_to_title_move]
    else:
        shutil.move(path_title_in, path_to_title_move)
    return [rel_path, None, None]


def move_same_name(path_input, path_output):
    path_to_title_move = uniquify(path_output)
    shutil.move(path_input, path_to_title_move)
    return path_to_title_move
          
def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        match = re.search(r'\((\d+)\)', filename)
        if match:
            num = [int(match.group(1)) for match in re.finditer(r'\((\d+)\)', filename)]
            if num:
                num = num[-1]
            else:
                num = 0
            num += 1
            filename = re.sub(r'\((\d+)\)', f'({num})', filename, 1)
        else:
            filename += f" ({counter})"
        path = f"{filename}{extension}"
    return path

def resize(filename, path_input):
    file = os.path.join(path_input, filename)
    temp_file = os.path.join(path_input, 'TEMP_IMAGES', f'temp_{filename}')
    im_file = BytesIO()

    try:
        shutil.copyfile(file, temp_file)
    except IOError:
        return resize_error(filename, path_input, "Copy error")

    ImageFile.LOAD_TRUNCATED_IMAGES = True

    try:
        img = Image.open(temp_file)
    except UnidentifiedImageError:
        img.close()
        cleanup_temp_file(temp_file)
        return resize_error(filename, path_input, "Unidentified image error")

    try:
        while os.path.getsize(temp_file) > 262144:
            width = int(img.size[0] / 4)
            ratio = (width / float(img.size[0]))
            height = int((float(img.size[1]) * float(ratio)))
            img = img.resize((width, height), Image.LANCZOS)
            save_temp_image(temp_file, img)
    except OSError as e:
        logging.error(f'OSError: {e}')
        img.close()
        cleanup_temp_file(temp_file)
        return resize_error(filename, path_input, "OSError")

    try:
        save_temp_image(im_file, img)
    except Exception as e:
        logging.error(f'Save image error: {e}')
        img.close()
        cleanup_temp_file(temp_file)
        return resize_error(filename, path_input, "Save image error")
    finally:
        img.close()
        cleanup_temp_file(temp_file)
    return im_file

def save_temp_image(file_path, img):
    try:
        if img.mode in ('JPEG', 'JFIF'):
            img.save(file_path, format="JPEG")
        elif img.mode == 'RGB':
            img.save(file_path, format="PNG")
        elif img.mode in ('RGBA', 'P', 'L', 'WEBP'):
            img.convert('RGB').save(file_path, format="PNG")
    except Exception as e:
        raise e

def cleanup_temp_file(temp_file):
    if os.path.exists(temp_file):
        os.remove(temp_file)

def resize_error(filename, path_input, error_message):
    logging.error(f'Error (PIL): {filename}\n{error_message}')
    move_error(filename, path_input)
    return



def check_dict(init_name, path_dict):
    with open(path_dict, 'r', encoding='utf-8') as custom_dict:
        custom_titles = json.load(custom_dict)
        title_name = None

        if isinstance(init_name, str):
            for (title, element) in custom_titles.items():
                for sub_element in element:
                    if sub_element in init_name.lower().replace(' ', ''):
                        title_name = title
                        break

            if title_name is None:
                title_name = (init_name[0].upper() + init_name[1:]).translate(str.maketrans(name_replacement))
                title_name = re.sub(r'\s+', ' ', title_name).strip()
                custom_titles[title_name] = [title_name.lower().replace(' ', '')]  # add value to dict

                with open(path_dict, 'w', encoding='utf-8') as write_dict:
                    json.dump(custom_titles, write_dict, ensure_ascii=False, indent=2)

        if isinstance(init_name, list):
            init_name = init_name[0]['alt'][6:].lower().replace(' ', '')
            for (title, element) in custom_titles.items():
                for sub_element in element:
                    if sub_element in init_name:
                        title_name = title
                        break
        if title_name is not None:
            title_name = title_name.strip()
        return title_name
