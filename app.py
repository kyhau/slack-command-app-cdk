#!/usr/bin/env python3
import json
import os

from aws_cdk import App, Environment

from slack_app_constructs_cdk.slack_app_constructs_stack import \
    SlackAppConstructsStack

env_file = os.environ.get("ENV_FILE", "env_dev.json")
with open(env_file) as json_file:
    stage_env = json.load(json_file)

app = App()
SlackAppConstructsStack(app, "K-CDK-SlackApp", env=Environment(**stage_env))
app.synth()
