
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import requests
from bs4 import BeautifulSoup

from config.config import *
from components.file_processing import *

def proxy_scrap(img_url, source):
    if source in proxy_dict:
        proxy_list = proxy_dict[source]
        
    for proxy in proxy_list:
        proxies = {'http': proxy, 'https': proxy}
        try:
            req = requests.get(img_url, proxies=proxies, headers=user_agent, timeout=5)
            if req.status_code == 200:
                return req
        except requests.RequestException:
            continue

    return None



def search_iqdb(filename, path_input, path_output, path_dict, is_sep_chars, is_dl_images):
    file = resize(filename, path_input).getvalue()
    file_data={'file': ('img', file)}
    req = requests.post('http://iqdb.org/',files=file_data,data=iqdb_payload)
    iqdb_request = BeautifulSoup(req.text, 'lxml')
    no_match = iqdb_request.find('div', class_='nomatch')
    if no_match is not None:
        return move_unknown(filename, path_input, path_output) 
    img_boxes = iqdb_request.find('div', id='pages', class_='pages')
    img_boxes_list = []
    if img_boxes is not None:
        img_boxes = list(img_boxes)
        for img_box in img_boxes:
            if img_box == img_boxes[0] or img_box == '\n' or str(img_box) == '<br/>':
                continue
            else:
                img_boxes_list.append(img_box)
        for img_box in img_boxes_list:
            try:
                source_box = img_box
                source_request = [None, None]
                source_name = source_box.find_all('tr')[2].text.strip().split(' ')[0]
                source_link = source_box.find('td', class_='image').find('a', href=True)['href']
                source_link_extra = source_box.find('span', class_='el') # danbooru/gelbooru
                if source_link_extra is not None:
                    source_link_extra = source_link_extra.find('a', href=True)['href']
                else:
                    source_link_extra = source_link
                if source_name is not None:
                    match source_name:
                        case 'Danbooru':
                            source_request = parse_danbooru(source_link, source_link_extra, path_dict)
                        case 'Gelbooru':
                            source_request = parse_gelbooru(source_link_extra, path_dict)
                        case 'Zerochan':
                            source_request = parse_zerochan(source_link, path_dict)
                        case 'yande.re':
                            source_request = parse_yandere(source_link, path_dict)
                        case 'e-shuushuu':
                            source_request = parse_eshuushuu(source_link, path_dict)
                        case 'Anime-Pictures':
                            source_request = parse_anime_pictures(source_link, path_dict)
                        case 'Konachan':
                            source_request = parse_konachan(source_link, path_dict)
                    if source_request is not None:
                        break
                else:              
                    continue
            except:
                if img_box == img_boxes_list[-1]:
                    return move_unknown(filename, path_input, path_output) 
                else: 
                    continue
        title_name = source_request[0]
        img_web = source_request[1]
        artist_name = source_request[2]
        character_name = source_request[3]
        if title_name is None and artist_name is None: 
            return move_unknown(filename, path_input, path_output)
        return move_images(title_name, filename, path_input, path_output, artist_name, character_name, img_web, is_sep_chars, is_dl_images, is_saucenao = False)
    return move_unknown(filename, path_input, path_output)

def parse_images_iqdb(request, domain):
    domain_parsers = {
        'danbooru.donmai.us': ('a', 'image-view-original-link', 'View original'),
        'gelbooru.com': ('ul', 'tag-list', 'Original image'),
        'e-shuushuu.net': ('a', 'thumb_image', None),
        'www.zerochan.net': ('a', 'preview', None),
        'yande.re': ('a', 'original-file-unchanged', None),
        'anime-pictures.net': ('a', 'get_image_link', None),
        'konachan.com': ('a', 'original-file-unchanged', None),
    }
    try:
        tag, class_name, string_value = domain_parsers.get(domain, (None, None, None))
        if tag is not None:
            img_box = request.find(tag, class_=class_name, href=True, string=string_value)
            img_web = img_box['href'] if img_box else None
        else:
            img_web = None
    except Exception:
        img_web = None

    return img_web

def parse_danbooru(img_url, img_url_extra, path_dict):
    title_name, img_web, artist_name, character_name = None, None, None, None
    img_url = f'https:{img_url}'
    if urlparse(img_url).netloc == 'danbooru.donmai.us':
        try:
            req = urlopen(img_url)
            if req.geturl() != img_url:
                raise Exception('URL redirected')
            else:
                danbooru_request = BeautifulSoup(req, 'lxml')
        except HTTPError as e:
            if e.code == 403:
                raise Exception('Image Removed')
        except OSError:
            raise Exception
            danbooru_request = BeautifulSoup(proxy_scrap(f'https:{img_url}', 'danbooru').content, 'lxml')
        
        title_box = danbooru_request.find('ul', class_='copyright-tag-list')
        if title_box:
            title_elements = title_box.find_all('a')[1].text
            title_elements_2 = title_box.find_all('a')[3].text if len(title_box.find_all('a')) > 3 else None
            title_elements = title_elements_2 if title_elements_2 == 'original' else title_elements
            title_name = check_dict(str(title_elements), path_dict)

        artist_box = danbooru_request.find('ul', class_='artist-tag-list')
        artist_name = artist_box.find_all('a')[1].text.strip() if artist_box else None

        character_box = danbooru_request.find('ul', class_='character-tag-list')
        if character_box:
            char_len = len(character_box.find_all('a'))
            if char_len == 2 or char_len == 4:
                character_name = character_box.find_all('a')[1].text.split('(')[0].strip().title()
                if char_len == 4 and character_box.find_all('a')[1].text == character_box.find_all('a')[3].text:
                    character_name = "MultiChar"
            elif char_len > 4:
                character_name = "MultiChar"

        img_web = parse_images_iqdb(danbooru_request, 'danbooru.donmai.us')

    else:
        img_url_to_use = img_url if img_url_extra is None else img_url_extra
        title_name, img_web = parse_gelbooru(img_url_to_use, path_dict)

    return [title_name, img_web, artist_name, character_name]

def parse_gelbooru(img_url_extra, path_dict):
    title_name, img_web, artist_name, character_name = None, None, None, None
    img_url_extra = f'https:{img_url_extra}'
    try:
        req = urlopen(Request(img_url_extra, headers=user_agent))
        if req.geturl() != img_url_extra:
            raise Exception('URL redirected')
        else:
            gelbooru_request = BeautifulSoup(req, 'lxml')
    except:  
        raise Exception
        gelbooru_request = BeautifulSoup(proxy_scrap(f'https:{img_url_extra}', 'gelbooru').content, 'lxml')

    title_box = gelbooru_request.find('li', class_='tag-type-copyright')
    if title_box:
        title_elements = title_box.find_all('a')[1].text
        title_elements_2 = title_box.find_all('a')[3].text if len(title_box.find_all('a')) > 3 else None
        title_elements = title_elements_2 if title_elements_2 == 'original' else title_elements
        title_name = check_dict(str(title_elements), path_dict)

    artist_box = gelbooru_request.find('li', class_='tag-type-artist')
    artist_name = artist_box.find_all('a')[1].text.strip() if artist_box else None

    character_box = gelbooru_request.find('li', class_='tag-type-character')  
    if character_box:
        char_len = len(character_box.find_all('a'))
        if char_len == 2 or char_len == 4:
            character_name = character_box.find_all('a')[1].text.split('(')[0].strip().title() 
            if char_len == 4 and character_box.find_all('a')[1].text == character_box.find_all('a')[3].text:
                character_name = "MultiChar"
        elif char_len > 4:
            character_name = "MultiChar"      

    img_web = parse_images_iqdb(gelbooru_request, 'gelbooru.com')
    return [title_name, img_web, artist_name, character_name]


def parse_yandere(img_url, path_dict):
    title_name, img_web, artist_name, character_name = None, None, None, None
    img_url = img_url.replace('http://', 'https://')
    try:
        req = urlopen(Request(img_url, headers=user_agent))
        if req.geturl() != img_url:
            raise Exception('URL redirected')
        else:
            yandere_request = BeautifulSoup(req, 'lxml')
    except:
        raise Exception
        yandere_request = BeautifulSoup(proxy_scrap(img_url, 'yandere').content, 'lxml')

    tags_box = yandere_request.find('li', class_='tag-type-copyright')
    if tags_box:
        tags_elements = tags_box.find_all('a')[1].text
        title_name = check_dict(str(tags_elements), path_dict)

    artist_box = yandere_request.find('li', class_='tag-type-artist')
    artist_name = artist_box.find_all('a')[1].text.strip() if artist_box else None

    character_box = yandere_request.find_all('li', class_='tag-type-character')
    if character_box:
        char_len = len(character_box)
        if char_len >= 1:
            character_name = character_box[0].find_all('a')[1].text.split('(')[0].strip().title() 
            if char_len == 2 and character_box[1].find_all('a')[1].text != character_name:
                character_name = "MultiChar"
        if char_len > 4:
            character_name = "MultiChar"

    img_web = parse_images_iqdb(yandere_request, 'yande.re')
    return [title_name, img_web, artist_name, character_name]

# tag-system | title-creation NO
def parse_zerochan(img_url, path_dict):
    title_name, img_web, artist_name, character_name = None, None, None, None
    img_url = img_url.replace('http://', 'https://')
    try:
        req = urlopen(Request(img_url, headers=user_agent))
        if req.geturl() != img_url:
            raise Exception('URL redirected')
        else:
            zerochan_request = BeautifulSoup(req, 'lxml')
    except:
        raise Exception
        zerochan_request = BeautifulSoup(proxy_scrap(img_url).content, 'lxml')

    img_box = zerochan_request.find('a', class_='preview', href=True) or zerochan_request.find('div', id='large')
    
    if img_box:
        tags_elements = img_box.find('img', alt=True)
        img_web = img_box['href'] if 'preview' in img_box['class'] else tags_elements['src']
        title_name = check_dict([tags_elements], path_dict)

    artist_box = zerochan_request.find('li', class_='mangaka')
    artist_name = artist_box.find('a').text.strip() if artist_name else None

    character_box = zerochan_request.find('li', class_='character primary')
    if character_box:
        character_name = character_box.find('a').text.split('(')[0].strip().title()
    else:
        character_box = zerochan_request.find_all('li', class_='character')
        char_len = len(character_box)

        if char_len == 1 or char_len == 2:
            character_name = character_box[0].find('a').text.split('(')[0].strip().title()

            if char_len == 2:
                character_name_sub = character_box[1].find('a').text.split('(')[0].strip().title()
                character_name = character_name_sub if character_name == character_name_sub else "MultiChar"
        elif char_len > 2:
            character_name = "MultiChar"

    return [title_name, img_web, artist_name, character_name]

def parse_eshuushuu(img_url, path_dict):
    title_name, character_name, artist_name, check_char = None, None, None, None
    img_url = img_url.replace('http://', 'https://')
    try:
        req = urlopen(Request(img_url, headers=user_agent))
        if req.geturl() != img_url:
            raise Exception('URL redirected')
        else:
            eshuushuu_request = BeautifulSoup(req, 'lxml')
    except:
        raise Exception
        eshuushuu_request = BeautifulSoup(proxy_scrap(img_url, 'eshuu').content, 'lxml')
    image_irl_id = img_url.split('/')[-2]  
    tags_box = eshuushuu_request.find('dd', id=f'quicktag2_{image_irl_id}')
    if tags_box is not None:
        tags_elements = tags_box.text.replace('"', '').replace('\n', '')
        title_name = check_dict(str(tags_elements), path_dict)
        try:
            check_char = tags_box.find_all('dt')[0].text.strip()
        except IndexError:
            chars_sh_box = eshuushuu_request.find_all('dt', text=lambda text: text and ('Characters:' in text or 'Old Characters:' in text))
            try:
                check_char = chars_sh_box[0].text.strip()
            except IndexError:
                check_char = None 
                
    if tags_box is None:
        title_name = "Original"    
                
    artist_box = eshuushuu_request.find('dd', id=f'quicktag3_{image_irl_id}')
    artist_name = artist_box.find_all('a')[0].text.strip() if artist_box else None           
        
    if check_char is not None and check_char == "Old Characters:":      
        char_len = len(character_name.split(','))
        if char_len == 1:
            character_name = tags_box.find_all('dt')[1].text.title()
        else:
            character_name = "MultiChar"       
                
    if check_char is not None and check_char == "Characters:":
        character_box = eshuushuu_request.find('dd', id=f'quicktag4_{image_irl_id}')
        if character_box is not None:
            char_len = len(character_box.find_all('a'))
            if char_len == 1:               
                character_name = character_box.find_all('a')[0].text.split('(')[0].strip().title() 
            else:
                character_name = "MultiChar"                                                                      
    img_web = parse_images_iqdb(eshuushuu_request, 'e-shuushuu.net')  
    return [title_name, img_web, artist_name, character_name]



def parse_anime_pictures(img_url, path_dict):
    title_name, character_name, artist_name = None, None, None
    img_url = f'https:{img_url}'
    try:
        req = urlopen(Request(img_url, headers=user_agent))
        if req.geturl() != img_url:
            raise Exception('URL redirected')
        else:
            anime_pic_request = BeautifulSoup(req, 'lxml')
    except:
        raise Exception
        anime_pic_request = BeautifulSoup(proxy_scrap(f'https:{img_url}', 'animepictures').content, 'lxml')

    title_elements = anime_pic_request.find('li', class_='svelte-bnip2f green')
    title_name = check_dict(str(title_elements.find('a').text.strip()), path_dict) if title_elements else None      

    artist_box = anime_pic_request.find('li', class_='svelte-bnip2f orange')
    artist_name = artist_box.find('a').text.strip() if artist_box else None
        

    character_box = anime_pic_request.find_all('li', class_='svelte-bnip2f blue')
    if character_box:
        char_len = len(character_box)

        if char_len >= 1:
            character_name = character_box[0].find('a').text.split('(')[0].strip().title()

        if char_len >= 2:
            character_name_sub = character_box[1].find('a').text.split('(')[0].strip().title()
            character_name = character_name_sub if character_name == character_name_sub else "MultiChar"

    img_web = parse_images_iqdb(anime_pic_request, 'anime-pictures.net')
    return [title_name, img_web, artist_name, character_name]


def parse_konachan(img_url, path_dict):
    title_name, character_name, artist_name = None, None, None
    img_url = f'https:{img_url}'
    try:
        req = urlopen(Request(img_url, headers=user_agent))
        if req.geturl() != img_url:
            raise Exception('URL redirected')
        else:
            konachan_request = BeautifulSoup(req, 'lxml')
    except:
        raise Exception
        konachan_request = BeautifulSoup(proxy_scrap(f'https:{img_url}', 'konachan').content, 'lxml')

    title_box = konachan_request.find('li', class_='tag-link tag-type-copyright')
    if title_box:
        title_elements = title_box.find_all('a')[1]
        if title_elements:
            title_name = check_dict(str(title_elements.text), path_dict)

    artist_box = konachan_request.find('li', class_='tag-link tag-type-artist')
    artist_name = artist_box.find_all('a')[1].text.strip() if artist_box else None
        
    character_box = konachan_request.find_all('li', class_='tag-link tag-type-character')
    if character_box is not None:   
        char_len = len(character_box)   
        if char_len == 1:
            character_name = character_box[0].find_all('a')[1].text.split('(')[0].strip().title() 
        if char_len == 2:
            character_name = character_box[0].find_all('a')[1].text.split('(')[0].strip().title() 
            character_name_sub = character_box[1].find_all('a')[3].text.split('(')[0].strip().title() 
            if character_name == character_name_sub:
                character_name = character_name_sub
            else:
                character_name = "MultiChar"
        if char_len > 2:
                character_name = "MultiChar"                       

    img_web = parse_images_iqdb(konachan_request, 'konachan.com')
    return [title_name, img_web, artist_name, character_name]
