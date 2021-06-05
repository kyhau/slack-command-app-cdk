# slack-command-app-cdk

[![githubactions](https://github.com/kyhau/slack-command-app-cdk/workflows/Build-Test/badge.svg)](https://github.com/kyhau/slack-command-app-cdk/actions)
[![travisci](https://travis-ci.org/kyhau/slack-command-app-cdk.svg?branch=master)](https://travis-ci.org/kyhau/slack-command-app-cdk)

This repo provides the source code for building a Slack App/Bot with AWS API Gateway and Lambda Functions, deploying with [CDK v2](https://docs.aws.amazon.com/cdk/latest/guide/work-with-cdk-v2.html) and testing wth SAM CLI ([sam-beta-cdk](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-cdk-getting-started.html)).
This SlackApp can handle requests triggered from a [Slash Command](https://api.slack.com/interactivity/slash-commands) which will take longer than [3 seconds](https://api.slack.com/events-api) to process, and posts the details back to the user.

### Overview

![Architecture](doc/SlackApp-ArchitectureOverview.png)

1. An API Gateway to provide an endpoint to be invoked from a Slack Command.
2. A Lambda Function [lambda/ImmediateResponse.py](lambda/ImmediateResponse.py) to perform authentication, some basic checks and send an intermediate response to Slack within 3 seconds (Slack requirement). This function invokes another Lambda function to to the request tasks (synchronously invocation for quick task; asynchronous invocation for long tasks).
3. A Lambda Function [lambda/AsyncWorker.py](lambda/AsyncWorker.py) to perform actual operation that may take more than 3 seconds to finish.
4. A Lambda Function [lambda/SyncWorker.py](lambda/SyncWorker.py) to perform actual operation that takes less than 3 seconds to finish.
6. CloudWatch Loggroup for API Gateway and Lambda Functions.

## Setup on Slack

To create a **Slack Command** in Slack (the default command in this repo is **`/testcdk`**)
1. Navigate to https://api.slack.com/apps.
2. Select **Create New App** and select **Slash Commands**.
3. Enter the name **`/testcdk`** for the command and click **Add Slash Command Integration**.
4. Enter the provided API endpoint URL in the URL field.
5. Copy the **Verification Token** from **Basic Information**.

## Build, Test and Deploy

Prerequisites
1. Install CDK v2: `npm install -g aws-cdk@next`
2. Update env_dev.json
3. Store your Slack token (from step (5) above) in the Parameter Store with [scripts/create_ssm_parameters.py](scripts/create_ssm_parameters.py).

```bash
# Create and activate virtual env (optional)

# Install requirements
pip install -e .

# First time
cdk bootstrap
# Or
cdk ls

cdk synth
```
### Test Lambda function locally with AWS SAM CLI and AWS CDK
Prerequisites:
1. Install [sam-beta-cdk](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-cdk-getting-started.html)
2. Start Docker

```bash
# Prepare the deployment artifacts
sam-beta-cdk build

# Invoke the function STACK_NAME/FUNCTION_IDENTIFIER
sam-beta-cdk local invoke K-CDK-SlackApp/K-CDK-SlackApp-ImmediateResponse -e tests/event_async.json
sam-beta-cdk local invoke K-CDK-SlackApp/K-CDK-SlackApp-ImmediateResponse -e tests/event_sync.json

# To start the API declared in the AWS CDK application
sam-beta-cdk local start-api

# To start a local endpoint that emulates AWS Lambda
sam-beta-cdk local start-lambda
```

For details of sam-beta-cdk, see https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-cdk-testing.html.

### Deploy

```bash
cdk deploy K-CDK-SlackApp

# If need to share the app with other Workspace, deploy also
cdk deploy K-CDK-SlackApp-OAuth

rm -rf cdk.out package */__pycache__ */*.egg-info */out.json
```

## Try it on Slack

E.g. if command is `/testcdk`, then

1. Run `/testcdk async`
1. Run `/testcdk sync`

## Notes on known sam-beta-cdk issues

1. KeyError when running `sam-beta-cdk ...`
   ```bash
   KeyError: '/home/.../lambda'
   Failed to execute script __main__
   ```
   - Known bug: https://github.com/aws/aws-sam-cli/issues/2849
   - Workaround:
       - Add `"@aws-cdk/core:newStyleStackSynthesis": false` into cdk.json
       - Add an empty requirements.txt to [lambda/](lambda/).
