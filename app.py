#!/usr/bin/env python3
import json
import os

from aws_cdk import App, Environment

from slack_app_constructs_cdk.slack_app_constructs_stack import \
    SlackAppConstructsStack
from slack_app_constructs_cdk.slack_app_oauth_constructs_stack import \
    SlackAppOAuthConstructsStack

ENV_STAGE = os.environ.get("ENV_STAGE", "dev")

with open(f"env_{ENV_STAGE}.json") as json_file:
    stage_env = json.load(json_file)

with open(f"settings_{ENV_STAGE}.json") as json_file:
    stage_settings = json.load(json_file)

app_name = stage_settings["name"]

app = App()

SlackAppConstructsStack(
    app,
    f"{app_name}-SlackApp",
    stage_settings,
    env=Environment(**stage_env)
)

SlackAppOAuthConstructsStack(
    app,
    f"{app_name}-SlackAppSharing",
    stage_settings,
    env=Environment(**stage_env)
)

app.synth()
