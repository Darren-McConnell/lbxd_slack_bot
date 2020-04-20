import dotenv
import json
import os
import slack
import time

from apscheduler.schedulers.background import BackgroundScheduler
from flask import abort, Flask, jsonify, request

# local import
from user_activity import UserActivity

dotenv.load_dotenv()

app = Flask(__name__)
slack_client = slack.WebClient(os.environ.get('SLACKBOT_TOKEN'))
lbxd_handler = UserActivity(
        lbxd_key=os.getenv('LBXD_API_KEY'),
        lbxd_secret=os.getenv('LBXD_SHARED_SECRET'))
scheduler = BackgroundScheduler()
film_chat_id = os.getenv('FILM_CHANNEL_ID')

@app.route('/add_user', methods=['POST'])
def add_user():
    message = lbxd_handler.add_user(request.form['text'])
    return jsonify(response_type='in_channel', text=message)

@app.route('/remove_user', methods=['POST'])
def remove_user():
    message = lbxd_handler.remove_user(request.form['text'])
    return jsonify(response_type='in_channel', text=message)

def format_block(activity):
    block = [{
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': activity['summary']
                }
            }]
    for d in activity['details']:
        section = {
            'type': 'section', 
            'fields': [
                {'type': 'mrkdwn', 'text': f'*{d["title"]}*'}, 
                {'type': 'mrkdwn', 'text': d['text']}
                ]
            }
        block.append(section)
        block.append({'type': 'divider'})

    return block

def activity_check():
    print('checking activities')
    activities = lbxd_handler.new_activities_check()
    print('activity check complete')
    if len(activities) == 0:
        print('no new activities')
    else:
        print('posting activities to slack')
        for a in activities:
            slack_client.chat_postMessage(
                    channel=film_chat_id, blocks=format_block(a))
        print('posting complete')

scheduler.add_job(activity_check, 'interval', minutes=1)
scheduler.start()
