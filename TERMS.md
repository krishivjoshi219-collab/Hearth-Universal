# Terms of Use — Hearth Universal

**Last updated:** October 2026

## 1. Nature of this project

Hearth Universal is an **open-source reference implementation** created for the
Build, Ship, Shape: Amazon Developer Hackathon (2026). It is provided for
educational and demonstration purposes. It is **not** an Amazon product, is not
endorsed by Amazon, and is not a certified Alexa+ add-on.

## 2. No warranty

This software is provided **"as is", without warranty of any kind**, express or
implied, including but not limited to warranties of merchantability, fitness for
a particular purpose, and non-infringement. See the [MIT License](LICENSE).

## 3. Safety model and its limits

Hearth enforces a *propose-never-execute* contract: consequential actions (spend,
physical security, climate boundaries) are staged as proposals and require explicit
human approval, with cryptographic receipts and 1-tap undo.

**This is a demonstration architecture, not a certified safety system.** Do **not**
connect it to real locks, real money, or safety-critical devices. The included
sandbox and guardrails have not been independently audited or verified for any
real-world deployment.

## 4. Simulated data

Unless you supply your own, all household state, sensor telemetry, product
catalogs, delivery tracking, energy tariffs, and neighbour nodes are **synthetic
fixtures**. Any savings figures, fairness scores, carbon estimates, or projected
costs these fixtures produce are illustrative modelling output. They are **not**
financial, engineering, or medical advice, and must not be used for planning.

## 5. Third-party services and model providers

- If you enable Amazon Bedrock, prompts are transmitted to AWS under your account
  and IAM policy, subject to the AWS Customer Agreement.
- Energy tariff rates, weather assumptions, and carbon factors are **hardcoded
  illustrative constants** for the region modelled in the demo, not live market
  data. Verify against your utility before relying on any figure.

## 6. Your responsibilities

You are responsible for:

- Complying with the [hackathon Official Rules](https://amazonappdev2026.devpost.com/rules)
  and the [Devpost Terms of Use](https://devpost.com/terms).
- Reviewing each staged proposal before approving it.
- Securing any AWS credentials you configure, and never committing them to a
  repository. A pre-commit secret scanner is included in CI.
- Complying with applicable privacy, consumer-protection, and building-safety law
  in your jurisdiction.

## 7. Limitation of liability

To the maximum extent permitted by law, the authors and contributors shall not be
liable for any claim, damages, losses, or other liability arising from the software
or its use, including any physical, financial, or data loss resulting from
connecting it to real-world systems.

## 8. Third-party trademarks

Amazon, Alexa, Alexa+, Amazon Bedrock, AgentCore, Strands, Fire TV, Ring, and
associated marks are trademarks of Amazon.com, Inc. or its affiliates. This project
is not affiliated with or endorsed by Amazon.

## 9. Changes

These terms may change as the project evolves. The version in the repository at
the time you use the software governs your use.

## 10. Contact

Questions via the [project repository](https://github.com/krishivjoshi219-collab/Hearth-Universal/issues).