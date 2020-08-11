


## Required software

You'll need to download and install the following software:

* [Python 3.7](https://www.python.org/downloads/)
* [Pipenv](https://pypi.org/project/pipenv/)
* [AWS CLI](https://aws.amazon.com/cli/)
* [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)

Make sure you have set up AWS credentials (typically placed under `~/.aws/credentials` or `~/.aws/config`). The credentials you're using should have "enough" privileges to provision all required services. You'll know the exact definition of "enough" when you get "permission denied" errors :)

Now, indicate which AWS profile should be used by the provided scripts, e.g,:

```bash
export AWS_PROFILE=[your-aws-profile]
```

## Python environment

Create the Python virtual environment and install the dependencies:

```bash
# from the project's root directory
pipenv --python 3.7 # creates Python 3.7 virtual environment
pipenv shell    # activate the virtual environment
pipenv install  # install dependencies
```

To know where the virtual environments and the dependencies are installed type this:

```bash
pipenv --venv
```

## Deploying the Solution

**Note:** At the time of this writing (July 2019), the Data API is publicly available in US East (N. Virginia), US East (Ohio), US West (Oregon), Europe (Ireland), and Asia Pacific (Tokyo) Regions.


### Deploying the Database

The deployment script reads the values from config file ```config-dev-env.sh``` (__important__: This file will be used everywhere! Make sure you edit the file with config value for your AWS account!).

Create (or reuse) an S3 bucket to store Lambda packages. Your AWS credentials must give you access to put objects in that bucket.

```
# Creating an S3 bucket (if needed)
aws s3 mb s3://[your-s3-bucket-name]
```

Make sure you update file `config-dev-env.sh` with the S3 bucket name otherwise the deployment will fail.

```bash
# Specifying the S3 bucket that will store Lambda package artifacts
export s3_bucket_deployment_artifacts="[your-s3-bucket-name]"
```

Now deploy the database resources by invoking the deploy script and passing the config file as an input parameter (__important__: Notice that we only specify the prefix of the config file (eg, `config-dev`) not the full file name).

```bash
# from project's root directory
./deploy_scripts/deploy_rds.sh config-dev
```

### Creating the Database entities (database and tables)

```bash
# from project's root directory
cd deploy_scripts/ddl_scripts
# run the script
./create_schema.sh config-dev
```

### Deploying the API

```bash
# from the project's root directory
./deploy_scripts/package_api.sh config-dev && ./deploy_scripts/deploy_api.sh config-dev
```

Upon completion, the deploy script will print the output parameters produced by the deployed API stack. Take note of the ```ApiEndpoint``` output parameter value.

## APIs



## Observability

We enabled observability of this application via [AWS X-Ray](https://aws.amazon.com/xray/). Take a look at the data access layer source file ([dal.py](https://github.com/aws-samples/aws-aurora-serverless-data-api-sam/blob/master/lambdas/helper/dal.py#L67)) for details. Search for terms `x-ray` and `xray`.

