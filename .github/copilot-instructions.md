# AWS Tagging Standards

All CloudFormation and CDK stacks must include these tags:

```yaml
tags: '[
  {"Key": "Branch", "Value": "${{ github.ref }}"},
  {"Key": "Hash", "Value": "${{ github.sha }}"},
  {"Key": "LastDeployUser", "Value": "${{ github.actor }}"},
  {"Key": "Repository", "Value": "https://github.com/${{ github.repository }}"},
  {"Key": "Scope", "Value": "account"}
]'
```

## Tag Definitions

- **Branch**: Git branch reference (e.g., `refs/heads/main`)
- **Hash**: Git commit SHA
- **LastDeployUser**: GitHub username who triggered deployment
- **Repository**: Full GitHub repository URL
- **Scope**: Resource scope (`account` for account-level resources)
