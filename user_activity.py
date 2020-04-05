import os
import csv
import datetime
import json
import letterboxd
import requests
import slack

# local imports
import config_utils
from lbxd_client import LbxdClient

URL_BASE = 'https://letterboxd.com/'
MAX_ACTIVITIES = 20
# Instead of using TRACKING_ACTIVITIES, it would be more effecient to use
# the ActivityRequest 'include' function to filter requests by activity type,
# but this is for paying lbxd members only.
# See api-docs.letterboxd.com/#/definitions/ActivityRequest for details.
TRACKING_ACTIVITIES = ['FilmRatingActivity', 'DiaryEntryActivity', 'ReviewActivity']

def format_url_link(url, text):
    return f'<{url}|{text}>'

def parse_film_link(activity):
    film_info = activity['film']
    title = f'{film_info["name"]} ({film_info["releaseYear"]})'
    url = next(l['url'] for l in film_info['links'] if l['type'] == 'letterboxd')
    return format_url_link(url, title)

def parse_user_link(activity):
    username = activity['member']['username']
    profile_link = URL_BASE + username
    return format_url_link(profile_link, f'*{username}*')

def parse_activity_link(activity, activity_key, text):
    link = activity[activity_key]['links'][0]['url']
    return format_url_link(link, text)

def parse_stars(activity):
    rating = activity.get('rating')
    if not rating:
        return '-'
    stars = '★ ' * int(rating)
    stars = stars + ('' if rating.is_integer() else '½')
    return stars

def parse_comment(activity):
    return activity['review']['lbml'] if activity['commentable'] else '-'

def build_details(activity, activity_key, detail_list):
    if activity_key:
        activity = activity[activity_key]

    func_dict = {
        "Film": parse_film_link,
        "Diary Date": (lambda a : a['diaryDetails']['diaryDate']),
        "Rating": parse_stars,
        "Comment": parse_comment
    }

    details = [{'title': d, 'text': func_dict[d](activity)} for d in detail_list]
    return details

def parse_activity(activity):
    activity_type = activity['type']
    user_link = parse_user_link(activity)

    if activity_type == 'FilmRatingActivity':
        sub_activity_key = None
        activity_type_str = 'Film Rating'
        detail_list = ['Film', 'Rating']
    elif activity_type == 'DiaryEntryActivity':
        sub_activity_key = 'diaryEntry'
        activity_type_str = parse_activity_link(activity, sub_activity_key, 'Diary Entry')
        detail_list = ['Film', 'Diary Date', 'Rating', 'Comment']
    elif activity_type == 'ReviewActivity':
        sub_activity_key = 'review'
        activity_type_str = parse_activity_link(activity, sub_activity_key, 'Review')
        detail_list = ['Film', 'Rating', 'Comment']
    else:
        return None

    summary = f'{user_link} added a {activity_type_str}:'
    details = build_details(activity, sub_activity_key, detail_list)

    return {"summary": summary, "details": details}

class UserActivity():
    def __init__(self, lbxd_key, lbxd_secret):
        self.lbxd_client = letterboxd.new(
                api_key=lbxd_key,
                api_secret=lbxd_secret)        

    @staticmethod
    def _get_lid(username):
        try:
            response = requests.get(URL_BASE + username)
        except requests.RequestException as error:
            print(error)

        if response.status_code == 404:
            print(f'User "{username}" not found')

        return response.headers.get('X-Letterboxd-Identifier')

    def add_user(self, username):
        user_config = config_utils.get_user_config()
        if username in user_config.keys():
            return f'"{username}" is already being tracked by lbxd_bot'

        lid = self._get_lid(username)
        if not lid:
            return f'Letterboxd user "{username}" doesn\'t appear to exist'

        user_config.update({username: {'lid': lid, 'last_update': ''}})
        config_utils.write_config(user_config)
        return f'"{username}" has been added to lbxd_bot'


    def remove_user(self, username):
        user_config = config_utils.get_user_config()
        if username not in user_config.keys():
            return f'"{username}" isn\'t being tracked by lbxd_bot'

        del user_config[username]
        config_utils.write_config(user_config)
        return f'"{username}" is no longer being tracked by lbxd_bot'


    def _get_user_activity(self, username):
        users = config_utils.get_user_config()
        lid = users[username]['lid']
        params_dict = {'where': 'OwnActivity', 'perPage': MAX_ACTIVITIES}
        activity_resp = self.lbxd_client.api.api_call(
                path=f'member/{lid}/activity',
                params=params_dict)
        return activity_resp.json()['items']

    def user_activities(self, username):
        users = config_utils.get_user_config()
        last_upd_time = users[username]['last_update']

        resp_json = self._get_user_activity(username)
        config_utils.set_config_value(
                username=username,
                field='last_update',
                value=resp_json[0]['whenCreated'])

        if not last_upd_time:
            return []

        new_items = [j for j in resp_json if 
                    (j['whenCreated'] > last_upd_time) & 
                    (j['type'] in TRACKING_ACTIVITIES)]
        parsed_activities = [parse_activity(i) for i in new_items]
        # remove nulls before returning
        return [p for p in parsed_activities if p]

    def new_activities_check(self):
        all_activity = []
        for u in config_utils.get_active_users():
            all_activity.extend(self.user_activities(u))
        return all_activity
