from aws_cdk import core as cdk
from model_deploy_construct import ModelDeploy


class AwsMlopAppStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deploy = ModelDeploy(
            self,
            id=construct_id,
            image_uri='939595455984.dkr.ecr.eu-west-1.amazonaws.com/dgl-citation-network:custom-torch-1.8',
            execution_role="arn:aws:iam::939595455984:role/kiarash-sagemaker",
        )
