import setuptools

with open("README.md") as fp:
    long_description = fp.read()

setuptools.setup(
    name="slack_app_constructs_cdk",
    version="0.2.1",
    description="A CDK Python app for deploying a Slack Command App and an OAuth 2.0 authorization flow service for sharing the Slack App",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kay Hau",
    package_dir={"": "slack_app_constructs_cdk"},
    packages=setuptools.find_packages(where="slack_app_constructs_cdk"),
    install_requires=[
        "aws-cdk-lib==2.202.0",
        "constructs==10.4.2",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 1 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
