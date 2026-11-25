# Cloud environment (Milestone 2, item 7)

One CloudFormation stack: [`claimsense-env.yaml`](claimsense-env.yaml). It passes `cfn-lint`.

| Resource | Name | Why |
|---|---|---|
| S3 bucket (encrypted, private, TLS-only, versioned) | `claimsense-dev-data-<account>` | synthetic data + clause index |
| ECR repository (scan on push, immutable tags) | `claimsense-dev` | images pushed only after the CI eval gate passes |
| DynamoDB table (on-demand, PITR, deletion protection) | `claimsense-dev-audit` | append-only audit log, key `request_id` |
| Secrets Manager secret | `claimsense/dev/openai-api-key` | OpenAI key; never in code |
| CloudWatch log group (30 days) | `/claimsense/dev/app` | logs, later p95 + alarm |
| Cognito user pool, web client, 4 role groups | `claimsense-dev-users` | identity for the access layer |
| IAM role (least privilege) | `claimsense-dev-app` | for the M3 ECS task |
| Budget alert, $20/month | `claimsense-dev-monthly` | cost guard |

Cost at rest is about **$0.40/month** (the secret). Everything else is pay-per-use. There's no compute yet; ECS is added in Milestone 3.

## Deploy (about 5 minutes, AWS CloudShell, no installs)

1. Sign in to the AWS console, set the region to **us-west-2 (Oregon)**, and open **CloudShell** (the `>_` icon, top bar).
2. **Actions → Upload file** → `infra/claimsense-env.yaml`.
3. Run:

```bash
aws cloudformation deploy \
  --stack-name claimsense-dev \
  --template-file claimsense-env.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides Env=dev BudgetEmail=you@example.com

aws cloudformation describe-stacks --stack-name claimsense-dev \
  --query "Stacks[0].Outputs" --output table
```

4. Upload the synthetic data (zip `data/` locally, upload the zip via CloudShell, then):

```bash
unzip data.zip && B=$(aws cloudformation describe-stacks --stack-name claimsense-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DataBucketName'].OutputValue" --output text)
aws s3 sync data/ s3://$B/ --exclude "schemas/*"
```

5. **Evidence for the checkpoint form:** screenshot CloudFormation → `claimsense-dev` → **Resources** tab (all `CREATE_COMPLETE`), plus the outputs table from step 3. Save it as `docs/evidence/aws-stack.png` in the repo.
6. Put the real OpenAI key in Secrets Manager → `claimsense/dev/openai-api-key` → *Retrieve secret value* → *Edit*. Do it in the console only; don't paste the key anywhere else.

## Tear down

```bash
aws dynamodb update-table --table-name claimsense-dev-audit --no-deletion-protection-enabled
aws s3 rm s3://$B --recursive   # versioned bucket: also delete versions in the console
aws cloudformation delete-stack --stack-name claimsense-dev
```
