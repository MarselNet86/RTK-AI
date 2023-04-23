import requests
from config import vk_token, openai_token
import openai
import pytz
from datetime import datetime

openai.api_key = openai_token

def get_wall_posts(group_name):
    url = f"https://api.vk.com/method/wall.get?domain={group_name}&count=2&access_token={vk_token}&v=5.81"
    response = requests.get(url).json()

    my_response = response['response']['items']
    date_1 = my_response[0]['date']
    date_2 = my_response[1]['date']

    if date_1 > date_2:
        post = response['response']['items'][0]
    else:
        post = response['response']['items'][1]

    array_photo = post

    if array_photo.get(['attachments'][0]):
        array_photo = array_photo['attachments'][0]
        if array_photo['type'] == 'photo':
            image = array_photo['photo']['sizes'][-1]['url']
        else:
            image = f"Не соответствует тип данных: {array_photo['type']}!"
    else:
        image = 'Отсутствует изображение!'

    post_id = post['id']
    post_text = post['text']
    timestamp = post['date']

    dt = datetime.fromtimestamp(timestamp)
    tz = pytz.timezone('Asia/Yekaterinburg')
    dt_ekb = tz.localize(dt)
    time = dt_ekb.strftime('%Y-%m-%d %H:%M:%S')

    return post_id, image, post_text, time


def get_group_info(group_name):
    url = f"https://api.vk.com/method/groups.getById?group_id={group_name}&access_token={vk_token}&v=5.131"
    response = requests.get(url).json()

    group = response['response'][0]

    group_id = group['id']
    group_name = group['name']
    group_screen_name = group['screen_name']

    return group_id, group_name, group_screen_name


def translate_to_english(message):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Translate this into English:\n\n{message}\n\n-",
        temperature=0.7,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=1
    )
    return response.choices[0].text.strip()


def get_extract(message):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=message + "\n\nTl;dr",
        temperature=0.7,
        max_tokens=60,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=1
    )
    return response.choices[0].text.strip()


def translate_to_russia(message):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Translate this into Russia:\n\n{message}\n\n-",
        temperature=0.7,
        max_tokens=700,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=1
    )
    return response.choices[0].text.strip()


def get_title(message):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Дайте краткий заголовок данному тексту, без кавычек: {message}",
        temperature=0.7,
        max_tokens=200,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    return response.choices[0].text.strip()



