import setuptools

with open("README.md") as fp:
    long_description = fp.read()

setuptools.setup(
    name="slack_app_constructs_cdk",
    version="0.3.0",
    description="A CDK Python app for deploying a Slack Command App and an OAuth 2.0 authorization flow service for sharing the Slack App",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kay Hau",
    package_dir={"": "slack_app_constructs_cdk"},
    packages=setuptools.find_packages(where="slack_app_constructs_cdk"),
    install_requires=[
        "aws-cdk-lib==2.238.0",
        "constructs==10.4.5",
    ],
    python_requires=">=3.13",
    classifiers=[
        "Development Status :: 1 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
