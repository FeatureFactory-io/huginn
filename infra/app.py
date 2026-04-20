import aws_cdk as cdk
from stacks.app_stack import AppStack
from stacks.cdn_stack import CdnStack
from stacks.data_stack import DataStack
from stacks.network_stack import NetworkStack

app = cdk.App()

env = cdk.Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region"),
)
domain = app.node.try_get_context("domain")

network = NetworkStack(app, "HuginnNetwork", env=env)
data = DataStack(app, "HuginnData", vpc=network.vpc, rds_sg=network.rds_sg, env=env)
app_stack = AppStack(app, "HuginnApp", vpc=network.vpc, eb_sg=network.eb_sg, env=env)
cdn = CdnStack(app, "HuginnCdn", domain=domain, env=env)

app.synth()
