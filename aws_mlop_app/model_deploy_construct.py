from attr import s
from datetime import datetime
from aws_cdk import core as cdk
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_stepfunctions_tasks as stepfunction_tasks
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam


class ModelDeploy(cdk.Construct):
    def __init__(self, scope: cdk.Construct, id: str, *, image_uri: str, execution_role: str, instance_type: str='m5.large') -> None:
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
        ecr_access_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "ecr:*"
            ],
        )

        ecr_access_policy.add_all_resources()


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

        # defining step function tasks
        # training task
        current_time = datetime.now().strftime("%I-%M-%B-%d-%Y")
        training_job = stepfunction_tasks.SageMakerCreateTrainingJob(
            self,
            id=f"Train the model",
            training_job_name=f"{id}TrainingJob{current_time}".lower(),
            algorithm_specification=training_algorithm,
            resource_config=training_resource,
            output_data_config=training_outputconfig,
            input_data_config=[training_dataset_channel],
            hyperparameters={
                'epochs': "10",
                'learning-rate': '0.01'
            },
            tags={
                "owner": "kiarash",
                "project": "cdk-test"
            },
            integration_pattern=stepfunctions.IntegrationPattern.RUN_JOB
        )

        training_job.grant_principal.add_to_principal_policy(ecr_access_policy)

        # creating model task
        create_model_job = stepfunction_tasks.SageMakerCreateModel(
            self,
            id="Create the model",
            model_name="zachary-club",
            primary_container=stepfunction_tasks.ContainerDefinition(
                image=stepfunction_tasks.DockerImage.from_registry(image_uri),
                model_s3_location=stepfunction_tasks.S3Location.from_bucket(artifact_bucket, key_prefix=f'output/{f"{id}TrainingJob{current_time}".lower()}/output/model.tar.gz'),
            )
        )

        create_model_job.grant_principal.add_to_principal_policy(ecr_access_policy)

        # createing endpoint configuration task
        endpoint_config_job = stepfunction_tasks.SageMakerCreateEndpointConfig(
            self,
            id="Create an endpoint configuration",
            endpoint_config_name="zachary-club",
            production_variants=[stepfunction_tasks.ProductionVariant(
                instance_type=ec2.InstanceType(instance_type),
                initial_instance_count=1,
                model_name="zachary-club",
                variant_name="test"
            )]
        )

        # creating endpoint task
        endpoint_job = stepfunction_tasks.SageMakerCreateEndpoint(
            self,
            id="Create an endpoint for the model",
            endpoint_config_name="zachary-club",
            endpoint_name="zachary-club",
        )

        states = training_job.next(create_model_job)
        states = states.next(endpoint_config_job)
        states = states.next(endpoint_job)
        state_machine = stepfunctions.StateMachine(
            self, 
            id="state-machine",
            definition=states
        )




