# Changelog

All notable changes to this project will be documented in this file.

## 0.2.1 - 2023-09-02

### Changed

* Updated Lambda Runtime from 3.8 to 3.11.
* Merged env_dev.json and settings_dev.json.

### Fixed

* Added missing setting `slack_app_id` to env_dev.json.


## 0.2.0 - 2021-06-05

### Added

* New stack `cdk deploy K-CDK-SlackApp-OAuth` to support OAuth 2.0 flow.


## 0.1.0 - 2021-05-15

### Added

Initial version
1. Implemented the CDK package [slack_app_constructs_cdk/](slack_app_constructs_cdk/) and app.py for creating
    1. An API Gateway to provide an endpoint to be invoked from a Slack Command.
    2. A Lambda Function [ImmediateResponse.py](lambda/ImmediateResponse.py) to perform authentication, some basic checks and send an intermediate response to Slack within 3 seconds (Slack requirement).
    3. A Lambda Function [AsyncWorker.py](lambda/AsyncWorker.py) to perform actual operation which may take more than 3 seconds to finish.
    4. A Lambda Function [SyncWorker.py](lambda/SyncWorker.py) to perform actual operation which will be finished in less than 3 seconds.
2. Added steps to test the Lambda code locally with sam-beta-cdk.
