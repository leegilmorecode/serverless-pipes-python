# serverless pipes python

An example of using Amazon EventBridge pipes with Python and the AWS CDK.

**NOTE: This is a basic example and is not production ready.**

![image](./docs/images/header.png)

The article can be found here: https://medium.com/@leejamesgilmore/serverless-eventbridge-pipes-309bdf209ecd

## Getting started

Top get started activiate the virtual environment

```
$ source .venv/bin/activate
```

Note: If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth --all
```

or deploy using the following

```
$ cdk deploy --all
```

To run the solution please look at the steps in the article linked above.

** The information and code provided are my own and I accept no responsibility on the use of the information. **
