#!/usr/bin/env python3
import json
import os

from aws_cdk import App, Environment

from slack_app_constructs_cdk.slack_app_constructs_stack import SlackAppConstructsStack
from slack_app_constructs_cdk.slack_app_oauth_constructs_stack import SlackAppOAuthConstructsStack

ENV_STAGE = os.environ.get("ENV_STAGE", "dev")

with open(f"env_{ENV_STAGE}.json") as json_file:
    stage_settings = json.load(json_file)

app_name = stage_settings["name"]

app = App()

SlackAppConstructsStack(
    app,
    id=f"{app_name}-SlackCommandApp",
    settings=stage_settings,
    env=Environment(account=stage_settings["account"], region=stage_settings["region"]),
)

SlackAppOAuthConstructsStack(
    app,
    id=f"{app_name}-SlackCommandAppSharing",
    settings=stage_settings,
    env=Environment(account=stage_settings["account"], region=stage_settings["region"]),
)

app.synth()
