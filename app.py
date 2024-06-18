#!/usr/bin/env python3
import os

import aws_cdk as cdk

from connect_llm.connect_llm_stack import ConnectLlmStack


app = cdk.App()
ConnectLlmStack(app, "CONNECT-LLM")

app.synth()
