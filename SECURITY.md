\# Security



\## Overview



LEGECY analyzes public Solana blockchain data and does not require private keys to analyze a wallet.



LEGECY must never request, store, log, or transmit:



\- Private keys

\- Seed phrases

\- Wallet recovery phrases

\- Signing keys

\- Exchange API secrets

\- Authentication tokens



Only public wallet addresses and public blockchain data should be used for wallet analysis.



\## Environment Variables



Sensitive configuration belongs in `.env`.



Never commit `.env` to Git.



The repository should contain only `.env.example`, which must contain placeholder or public-safe values.



\## RPC Configuration



LEGECY uses a Solana RPC endpoint through the `SOLANA\_RPC\_URL` environment variable.



For production deployments:



\- Use a reliable RPC provider.

\- Keep provider API keys/secrets in environment variables.

\- Do not hard-code credentials in source code.

\- Do not expose RPC credentials to the frontend.



\## API Security



The FastAPI service should be deployed behind a trusted reverse proxy or managed platform in production.



Production deployments should use:



\- HTTPS

\- Restricted CORS origins

\- Rate limiting

\- Request validation

\- Appropriate logging

\- Secret management through environment variables



Development settings such as unrestricted CORS should not automatically be treated as production configuration.



\## Wallet Data



Wallet addresses are public blockchain information.



Generated wallet profiles may contain derived analytical information and should be treated as application data.



Do not store private credentials alongside wallet profiles.



\## Reporting a Vulnerability



If you discover a security vulnerability in LEGECY, do not publicly disclose sensitive details before the issue has been investigated.



Provide:



1\. A description of the vulnerability

2\. Steps to reproduce it

3\. Potential impact

4\. Any relevant logs or proof of concept



\## Security Principle



LEGECY should follow a simple rule:



> Analyze public blockchain data. Never handle private wallet credentials.

