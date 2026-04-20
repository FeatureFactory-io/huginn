from pathlib import Path

from aws_cdk import CustomResource, Duration, Stack
from aws_cdk import (
    aws_certificatemanager as acm,
)
from aws_cdk import (
    aws_cloudfront as cloudfront,
)
from aws_cdk import (
    aws_cloudfront_origins as origins,
)
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import (
    aws_route53 as route53,
)
from aws_cdk.custom_resources import Provider
from constructs import Construct

_LAMBDA_DIR = Path(__file__).resolve().parent.parent / "lambda" / "route53_cname"


class CdnStack(Stack):
    """ACM certificate, CloudFront distribution, and Route53 CNAME for huginn.

    DNS authority boundary: the featurefactory.io hosted zone is pre-existing
    and not managed by CDK. The huginn CNAME is applied via a custom resource
    that UPSERTs only when the record is missing or points somewhere other than
    the active CloudFront domain (avoids "already exists" failures when the
    record still targets Elastic Beanstalk).

    To deploy (Phase 1):
        make infra-deploy-cdn
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        domain: str,
        # Pass a pre-constructed zone in tests to skip the AWS lookup call.
        hosted_zone: route53.IHostedZone | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if hosted_zone is None:
            hosted_zone = route53.HostedZone.from_lookup(
                self,
                "Zone",
                domain_name=domain,
            )

        cert = acm.Certificate(
            self,
            "Cert",
            domain_name=domain,
            subject_alternative_names=[f"*.{domain}"],
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # HSTS at the edge so browsers see it even before the EB app is redeployed
        # with Django SECURE_HSTS_* (same 1h starter as production.py).
        hsts_policy = cloudfront.ResponseHeadersPolicy(
            self,
            "HstsHeaders",
            security_headers_behavior=cloudfront.ResponseSecurityHeadersBehavior(
                strict_transport_security=cloudfront.ResponseHeadersStrictTransportSecurity(
                    access_control_max_age=Duration.seconds(3600),
                    override=True,
                    include_subdomains=True,
                ),
            ),
        )

        distribution = cloudfront.Distribution(
            self,
            "Cdn",
            domain_names=[f"huginn.{domain}"],
            certificate=cert,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(
                    "huginn-prod.us-east-1.elasticbeanstalk.com",
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                response_headers_policy=hsts_policy,
            ),
        )

        on_event_fn = lambda_.Function(
            self,
            "Route53CnameFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.on_event",
            code=lambda_.Code.from_asset(str(_LAMBDA_DIR)),
            timeout=Duration.minutes(2),
        )

        on_event_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "route53:ListResourceRecordSets",
                    "route53:ChangeResourceRecordSets",
                ],
                resources=[
                    f"arn:aws:route53:::hostedzone/{hosted_zone.hosted_zone_id}",
                ],
            )
        )

        provider = Provider(self, "Route53CnameProvider", on_event_handler=on_event_fn)

        record_fqdn = f"huginn.{domain}."
        cname_resource = CustomResource(
            self,
            "HuginnCnameResource",
            service_token=provider.service_token,
            properties={
                "HostedZoneId": hosted_zone.hosted_zone_id,
                "RecordName": record_fqdn,
                "TargetDomain": distribution.distribution_domain_name,
                "Ttl": "300",
            },
        )
        cname_resource.node.add_dependency(distribution)
