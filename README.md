# lbxd_slack_bot

## Installation

Clone repo:
`git clone https://github.com/Darren-McConnell/lbxd_slack_bot.git`  

Install third party requirements:
`pip3 install -r requirements.txt`

## Slack bot set-up

Navigate to the [_Your Apps_](https://api.slack.com/apps?new_app=1) section from Slack's API hub, click _Create New App_ and set an app name and target workspace.

In the _OAuth & Permissions_ section, add the Bot Token Scopes `chat:write` & `commands`. Click on Install App to Workspace and allow access.

You need to configure 2 slash commands to interact with the app, but you'll need a target host address first. If you want to test locally, you can use a secure tunnelling service to test. Ngrok is a simple tool for this use case.

## Testing with Ngrok

Download and install [from here](https://ngrok.com/download). Once installed, start it up and run: `Ngrok http 5000`.

## Slack slash Commands

In the Slack app _Slash Commands_ sections, add 2 commands for `/add_user` and `/remove_user`. Both commands take 1 argument (a letterboxd username).

Set the _Request URL_ to the Ngrok endpoint, so for `/add_user`, the url should be `http://xxxxxxxx.ngrok.io/add_user`.

## Environment Variables

Before running the app, you need to add tokens and signing secrets for both the letterboxd API and slack bot to the `.env` file:

*  `SLACKBOT_TOKEN` = _Slack app hub_ -> _OAuth & Permissions_ -> _Bot User OAuth Access Token_

*  `SLACK_SIGNING_SECRET` = _Slack app hub_ -> _Basic Information_ -> _Signing Secret_

* As the letterboxd API is still in beta, you'll need to request access from their API team to receive the `LBXD_API_KEY` and `LBXD_SHARED_SECRET`. [See here](https://letterboxd.com/api-beta/) for details.

## Running with flask
Flask will use the `FLASK_APP` variable specified in the `.env` file to run the `lbxd_slack_bot.py` script.

Simply navigate to the base repo folder and execute `flask run`.

Once up and running, try adding a letterboxd user with the `/add_user {letterboxd_username}` command in the Slack workspace the app was installed in to start tacking their activities.

The bot will then track any reviews, diary entries or film ratings made by that user and post a summary to the Slack workspace.
