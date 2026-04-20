from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class NetworkStack(Stack):
    """VPC, subnets, and security groups for all Huginn services.

    Exports:
        vpc     — used by DataStack (RDS subnet placement) and AppStack (EB placement)
        eb_sg   — EB EC2 instance security group; passed to AppStack
        rds_sg  — RDS security group; passed to DataStack
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            nat_gateways=1,  # cost-saving: 1 NAT; bump to max_azs for HA
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # EB EC2 instances: inbound HTTP from internet, full outbound
        self.eb_sg = ec2.SecurityGroup(
            self,
            "EbSg",
            vpc=self.vpc,
            description="Huginn EB EC2 — inbound HTTP from anywhere",
            allow_all_outbound=True,
        )
        self.eb_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="HTTP from internet (CloudFront origin request)",
        )

        # RDS: inbound PostgreSQL from EB SG only, no outbound
        self.rds_sg = ec2.SecurityGroup(
            self,
            "RdsSg",
            vpc=self.vpc,
            description="Huginn RDS — inbound PostgreSQL from EB only",
            allow_all_outbound=False,
        )
        self.rds_sg.add_ingress_rule(
            peer=self.eb_sg,
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL from EB security group",
        )
