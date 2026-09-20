# Security Policy

## Deployment model

The Vercel-facing NexaRAG portfolio demo is intentionally static and contains no API keys, access tokens, credentials, or production secrets.

The full NexaRAG RAG runtime is designed for local execution with Ollama. Local document data and vector indexes should not be committed to Git.

## Security practices

- Never commit API keys, tokens, passwords, private documents, or local vector-store data.
- Keep secrets in local environment files that are ignored by Git, or in Vercel Environment Variables when a cloud service is added.
- Never expose secrets through variables prefixed with `NEXT_PUBLIC_`.
- Use separate credentials for development, preview, and production.
- Rotate any credential immediately if it is accidentally committed.
- Review dependency updates and CI results before production changes.
- Keep Vercel Deployment Protection and Git fork protection enabled where supported.
- Use rate limiting and WAF rules before exposing future dynamic API routes publicly.

## Reporting a vulnerability

Please do not open a public issue containing credentials, exploit details, or private data. Use a private contact channel with the repository owner instead.
