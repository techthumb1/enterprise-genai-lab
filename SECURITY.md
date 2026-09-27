# Security Policy

## Reporting

Please report vulnerabilities privately through GitHub's security advisory feature. Do not open a public issue containing credentials, exploit details, private documents, or personal data.

## Credential handling

- Never commit `.env`, API keys, database passwords, cloud credentials, tokens, or private keys.
- Use `.env.example` only for names and non-secret defaults.
- Inject production secrets through the deployment platform's secret manager.
- Rotate any value immediately if it is accidentally exposed and remove it from Git history.

## Scope

This repository is a reference implementation. Public production use additionally requires authentication, authorization, rate limiting, CORS policy, network controls, approved telemetry, retention rules, and security review.
