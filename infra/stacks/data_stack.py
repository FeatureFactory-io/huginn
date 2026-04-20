from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk import aws_ssm as ssm
from constructs import Construct

# SSM params that do NOT yet exist in AWS — CDK creates placeholder stubs.
# Set real values via: aws ssm put-parameter --name /huginn/prod/<NAME> \
#   --value '<value>' --type SecureString --overwrite
# Secrets never go into CDK code.
#
# Already-existing params (created manually, not owned by CDK yet):
#   /huginn/prod/SECRET_KEY       — import in Phase 2 via `cdk import`
#   /huginn/prod/POSTGRES_PASSWORD — import in Phase 2 via `cdk import`
_SSM_NEW_PARAMS = [
    "POSTGRES_USER",
    "GITLAB_TOKEN",
    "JIRA_TOKEN",
    "LLM_API_KEY",
]


class DataStack(Stack):
    """RDS PostgreSQL 16 (private subnet) and SSM parameter stubs.

    RemovalPolicy.RETAIN is set on all data resources — destroying the stack
    must never destroy production data.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.Vpc,
        rds_sg: ec2.SecurityGroup,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        subnet_group = rds.SubnetGroup(
            self,
            "SubnetGroup",
            description="Huginn RDS — private subnets only",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.db = rds.DatabaseInstance(
            self,
            "Postgres",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_16),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[rds_sg],
            subnet_group=subnet_group,
            database_name="huginn",
            removal_policy=RemovalPolicy.RETAIN,
            deletion_protection=True,
            backup_retention=Duration.days(7),
            multi_az=False,  # single-AZ adequate for team of 2-5; enable for HA
            storage_encrypted=True,
        )

        for name in _SSM_NEW_PARAMS:
            ssm.StringParameter(
                self,
                f"Param{name.replace('_', '').title()}",
                parameter_name=f"/huginn/prod/{name}",
                string_value="REPLACE_ME",
                description=f"Huginn production {name} — replace value manually, never via CDK",
            )
