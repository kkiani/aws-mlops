#!/usr/bin/env python3
import os

from aws_cdk import core as cdk
from aws_mlop_app.aws_mlop_app_stack import AwsMlopAppStack


app = cdk.App()
AwsMlopAppStack(app, "AwsMlopAppStack")

app.synth()
