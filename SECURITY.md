# Security Policy

## Reporting

Please report vulnerabilities privately through GitHub's security advisory feature. Do not open a public issue containing credentials, exploit details, private documents, or personal data.

## Credential handling

- Never commit `.env`, API keys, database passwords, cloud credentials, tokens, or private keys.
- Use `.env.example` only for names and non-secret defaults.
- Inject production secrets through the deployment platform's secret manager.
- Rotate any value immediately if it is accidentally exposed and remove it from Git history.
- Keep provider and database credentials server-side; the browser bundle must use relative API calls and contain no secrets.

## Sensitive application data

The governed answer endpoint omits raw evidence and unreleased candidates. Review list/detail endpoints intentionally expose both for authorized review and must be protected as sensitive document access. Do not rely on a user-entered reviewer ID as authentication.

## Scope

This repository is a reference implementation. Public production use additionally requires authentication, reviewer and processing-run authorization, rate limiting, CORS and content-security policy, network controls, approved telemetry, retention rules, and security review.
