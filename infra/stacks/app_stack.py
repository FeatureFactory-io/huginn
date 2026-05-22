from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_cloudwatch as cw,
)
from aws_cdk import (
    aws_ec2 as ec2,
)
from aws_cdk import (
    aws_ecr as ecr,
)
from aws_cdk import (
    aws_elasticbeanstalk as eb,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_logs as logs,
)
from constructs import Construct

# Verified from `aws elasticbeanstalk describe-environments` on 2026-04-17.
# Update if EB rolls the platform: aws elasticbeanstalk list-available-solution-stacks \
#   --query 'SolutionStacks[?contains(@,`Docker`) && contains(@,`2023`)]'
EB_SOLUTION_STACK = "64bit Amazon Linux 2023 v4.12.1 running Docker"

EB_ENVS = ["huginn-blue", "huginn-green"]

# Log file paths that EB log streaming creates under /aws/elasticbeanstalk/{env}/.
# Matches the paths already live on mimir-prod/mimir-idle (verified 2026-05-22).
EB_LOG_SUFFIXES = [
    "var/log/eb-docker/containers/eb-current-app/stdouterr.log",
    "var/log/docker",
    "var/log/docker-events.log",
    "var/log/docker-compose-events.log",
    "var/log/nginx/access.log",
    "var/log/nginx/error.log",
    "var/log/eb-engine.log",
]


class AppStack(Stack):
    """ECR, EB application + blue/green environments, IAM, and CloudWatch alarms.

    EB environments are *infrastructure-only* — CDK owns platform, VPC placement,
    instance type, and static env properties. Application version deployment
    (Docker image SHA) continues to be managed by scripts/deploy-staging.sh and promote-prod.sh.

    Resource names match existing AWS resources exactly for cdk import (Phase 2/4):
      ECR repo       huginn
      EB app         huginn
      EB envs        huginn-blue, huginn-green
      IAM user       huginn-ci
      IAM role       aws-elasticbeanstalk-ec2-role
      IAM profile    aws-elasticbeanstalk-ec2-role
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.Vpc,
        eb_sg: ec2.SecurityGroup,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── ECR ──────────────────────────────────────────────────────────────
        self.ecr_repo = ecr.Repository(
            self,
            "EcrRepo",
            repository_name="huginn",
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    max_image_count=20,
                    description="Keep last 20 images to cap storage cost",
                ),
            ],
        )

        # ── IAM: EB instance role ─────────────────────────────────────────────
        # Matches the existing role `aws-elasticbeanstalk-ec2-role` exactly.
        # Managed policies verified via `aws iam list-attached-role-policies`.
        instance_role = iam.Role(
            self,
            "EbInstanceRole",
            role_name="aws-elasticbeanstalk-ec2-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSElasticBeanstalkWebTier"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSElasticBeanstalkWorkerTier"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSElasticBeanstalkMulticontainerDocker"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
            ],
        )

        instance_profile = iam.CfnInstanceProfile(
            self,
            "EbInstanceProfile",
            instance_profile_name="aws-elasticbeanstalk-ec2-role",
            roles=[instance_role.role_name],
        )

        # ── IAM: GitLab CI deploy user ────────────────────────────────────────
        # Matches existing user `huginn-ci` with attached `huginn-ci-policy`.
        deploy_user = iam.User(
            self,
            "GitlabDeployUser",
            user_name="huginn-ci",
        )

        deploy_policy = iam.ManagedPolicy(
            self,
            "GitlabDeployPolicy",
            managed_policy_name="huginn-ci-policy",
            statements=[
                iam.PolicyStatement(
                    sid="ECRAuth",
                    actions=["ecr:GetAuthorizationToken"],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="ECRPush",
                    actions=[
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "ecr:PutImage",
                        "ecr:InitiateLayerUpload",
                        "ecr:UploadLayerPart",
                        "ecr:CompleteLayerUpload",
                    ],
                    resources=[self.ecr_repo.repository_arn],
                ),
                iam.PolicyStatement(
                    sid="EBDeploy",
                    actions=[
                        "elasticbeanstalk:*",
                        "ec2:Describe*",
                        "ec2:CreateSecurityGroup",
                        "ec2:CreateTags",
                        "elasticloadbalancing:*",
                        "autoscaling:*",
                        "cloudwatch:*",
                        "cloudformation:*",
                        "s3:*",
                        "logs:*",
                        "iam:PassRole",
                        "iam:GetRole",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="SSMSecrets",
                    actions=["ssm:GetParameter", "ssm:GetParameters"],
                    resources=[f"arn:aws:ssm:{self.region}:{self.account}:parameter/huginn/*"],
                ),
            ],
        )
        deploy_user.add_managed_policy(deploy_policy)

        # ── EB Application ────────────────────────────────────────────────────
        eb_app = eb.CfnApplication(
            self,
            "EbApp",
            application_name="huginn",
            description="Human-AI OODA composite for engineering PMs",
        )

        # ── EB Environments (blue/green) ──────────────────────────────────────
        public_subnet_ids = vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnet_ids

        for env_name in EB_ENVS:
            env_resource = eb.CfnEnvironment(
                self,
                f"EbEnv{env_name.replace('-', '').title()}",
                application_name=eb_app.ref,
                environment_name=env_name,
                cname_prefix=env_name,
                solution_stack_name=EB_SOLUTION_STACK,
                option_settings=[
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:elasticbeanstalk:environment",
                        option_name="EnvironmentType",
                        value="SingleInstance",
                    ),
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:elasticbeanstalk:environment",
                        option_name="ServiceRole",
                        value="aws-elasticbeanstalk-service-role",
                    ),
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:autoscaling:launchconfiguration",
                        option_name="InstanceType",
                        value="t3.small",
                    ),
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:autoscaling:launchconfiguration",
                        option_name="IamInstanceProfile",
                        value=instance_profile.ref,
                    ),
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:autoscaling:launchconfiguration",
                        option_name="DisableIMDSv1",
                        value="true",
                    ),
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:autoscaling:launchconfiguration",
                        option_name="SecurityGroups",
                        value=eb_sg.security_group_id,
                    ),
                    # VPC placement (Phase 4: CDK-managed VPC replaces default VPC)
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:ec2:vpc",
                        option_name="VPCId",
                        value=vpc.vpc_id,
                    ),
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:ec2:vpc",
                        option_name="Subnets",
                        value=",".join(public_subnet_ids),
                    ),
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:ec2:vpc",
                        option_name="AssociatePublicIpAddress",
                        value="true",
                    ),
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:elasticbeanstalk:application",
                        option_name="Application Healthcheck URL",
                        value="/health/",
                    ),
                    # CloudWatch log streaming — streams all container stdout/stderr
                    # and platform logs to /aws/elasticbeanstalk/{env}/var/log/...
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:elasticbeanstalk:cloudwatch:logs",
                        option_name="StreamLogs",
                        value="true",
                    ),
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:elasticbeanstalk:cloudwatch:logs",
                        option_name="RetentionInDays",
                        value="30",
                    ),
                    eb.CfnEnvironment.OptionSettingProperty(
                        namespace="aws:elasticbeanstalk:cloudwatch:logs",
                        option_name="DeleteOnTerminate",
                        value="false",
                    ),
                ],
            )
            env_resource.add_dependency(eb_app)

        # ── CloudWatch: log groups for both EB environments ───────────────────
        # Pre-create all log groups that EB streaming populates so CDK controls
        # retention policy. EB reuses existing groups rather than creating new ones.
        # Names match the fixed paths the AL2023/Docker platform uses (verified
        # against mimir-prod which uses the same platform).
        stdouterr_log_groups: list[logs.LogGroup] = []

        for env_name in EB_ENVS:
            env_slug = env_name.replace("-", "")  # e.g. "huginnblue"
            for suffix in EB_LOG_SUFFIXES:
                # Build a unique CDK construct ID from env + suffix path components.
                suffix_slug = suffix.replace("/", "").replace(".", "").replace("-", "")
                lg = logs.LogGroup(
                    self,
                    f"LG{env_slug}{suffix_slug}",
                    log_group_name=f"/aws/elasticbeanstalk/{env_name}/{suffix}",
                    retention=logs.RetentionDays.ONE_MONTH,
                    removal_policy=RemovalPolicy.RETAIN,
                )
                if suffix == "var/log/eb-docker/containers/eb-current-app/stdouterr.log":
                    stdouterr_log_groups.append(lg)

        # ── CloudWatch: application error alarm ───────────────────────────────
        # One MetricFilter per env; both publish to Huginn/AppErrors so a single
        # alarm covers blue and green. Logs are JSON-structured with "level" key.
        for idx, lg in enumerate(stdouterr_log_groups):
            logs.MetricFilter(
                self,
                f"AppErrorFilter{idx}",
                log_group=lg,
                filter_pattern=logs.FilterPattern.literal('{ $.level = "ERROR" }'),
                metric_namespace="Huginn",
                metric_name="AppErrors",
                metric_value="1",
                default_value=0,
            )

        cw.Alarm(
            self,
            "AppErrorAlarm",
            alarm_name="huginn-app-error-rate",
            alarm_description="More than 2 ERROR log entries in 1 hour across either EB env",
            metric=cw.Metric(
                namespace="Huginn",
                metric_name="AppErrors",
                period=Duration.hours(1),
                statistic="Sum",
            ),
            threshold=2,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
