#!/usr/bin/env python3
import os

import aws_cdk as cdk
from stateful.stateful import DentistsStatefulStack
from stateless.stateless import DentistsStatelessStack

app = cdk.App()

# we split our app into stateful and stateless resources
DentistsStatefulStack(app, "DentistsStatefulStack")
DentistsStatelessStack(app, "DentistsStatelessStack")

app.synth()
