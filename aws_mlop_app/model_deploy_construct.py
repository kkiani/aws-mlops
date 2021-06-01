from attr import s
from aws_cdk import core as cdk
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_stepfunctions_tasks as stepfunction_tasks
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ec2 as ec2


class ModelDeploy(cdk.Construct):
    def __init__(self, scope: cdk.Construct, id: str, *, image_uri: str, execution_role: str, instance_type: str='ml.m5.large') -> None:
        super().__init__(scope, id)
        
        # creating bucket to save model artifacts in it.
        artifact_bucket = s3.Bucket(
            self,
            id=f"{id}-bucket",
            bucket_name=f"{id.lower()}",
            removal_policy=cdk.RemovalPolicy.DESTROY
        )


        # policy
        # TODO: the policy must be removed when the whole architecture is desgined.
        training_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "ecr:*"
            ],
        )

        training_policy.add_all_resources()


        # creating training job process with sagemaker
        training_algorithm = stepfunction_tasks.AlgorithmSpecification(
            training_image=stepfunction_tasks.DockerImage.from_registry(image_uri)
        )

        training_outputconfig = stepfunction_tasks.OutputDataConfig(
            s3_output_location=stepfunction_tasks.S3Location.from_bucket(artifact_bucket, key_prefix='output')
        )

        training_resource = stepfunction_tasks.ResourceConfig(
            instance_count=1,
            instance_type=ec2.InstanceType(instance_type),
            volume_size=cdk.Size.gibibytes(10)
        )

        training_dataset_channel = stepfunction_tasks.Channel(
            channel_name="training-data",
            data_source=stepfunction_tasks.DataSource(
                s3_data_source=stepfunction_tasks.S3DataSource(
                    s3_location=stepfunction_tasks.S3Location.from_bucket(artifact_bucket, key_prefix="input")
                )
            )
        )

        training_job = stepfunction_tasks.SageMakerCreateTrainingJob(
            self,
            id=f"training-job",
            training_job_name=f"{id}TrainingJob".lower(),
            # role=execution_role,
            algorithm_specification=training_algorithm,
            resource_config=training_resource,
            output_data_config=training_outputconfig,
            input_data_config=[training_dataset_channel],
            hyperparameters={
                'epochs': "100",
                'learning-rate': '0.01'
            },
            tags={
                "owner": "kiarash",
                "project": "cdk-test"
            }
        )

        state_machine = stepfunctions.StateMachine(
            self, 
            id="state-machine",
            definition=training_job
        )


