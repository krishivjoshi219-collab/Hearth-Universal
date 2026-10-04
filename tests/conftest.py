"""Shared pytest configuration.

Test isolation
--------------
The household engines persist to `state/` (proposals, audit chain, AgentCore
memory, goals). By default the suite therefore appends to whatever the running
demo server has already written, which causes two problems:

1. **Order-dependent failures.** Once the audit chain and proposal store grow,
   assertions that reason about "the" pending proposal or a replayed decision
   start depending on leftover demo state.
2. **Quadratic slowdown.** `audit.append` re-reads the tail of the chain on every
   call to find the previous hash. Against a multi-megabyte chain that dominates
   the run time -- the suite went from ~61s to ~160s purely from accumulated
   local state.

Both are fixed by pointing every test at a throwaway state directory.

This must happen at *import* time, not in a fixture: `hearth.audit` binds
`STATE_DIR` at module scope, so the environment has to be set before any test
module imports `hearth`.
"""
import os
import shutil
import tempfile

_TEST_STATE = tempfile.mkdtemp(prefix="hearth-test-state-")
os.environ["HEARTH_STATE_DIR"] = _TEST_STATE
# Keep background schedulers/heartbeat quiet and deterministic under test.
os.environ.setdefault("HEARTH_DISABLE_SCHEDULER", "1")

# Offline AWS posture.
#
# Constructing a `strands.Agent` builds a BedrockModel, which builds a boto3
# client. With no credentials and no AWS_EC2_METADATA_DISABLED, boto3 probes the
# EC2 instance metadata endpoint and blocks until it times out -- roughly 8s per
# agent construction, which dominated the suite once the Strands tests landed.
#
# Dummy credentials plus IMDS disabled make client construction instant and
# fully offline. This cannot accidentally enable live inference: the Bedrock
# path is additionally gated on AWS_BEDROCK_ENABLED, pinned to "0" here.
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test-not-a-real-key")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test-not-a-real-secret")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ["AWS_BEDROCK_ENABLED"] = "0"


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TEST_STATE, ignore_errors=True)