# Security

The Orrery plug-ins read their own preset files (`.positron`, `.scorpius`, `.wraith`) and the state a host saves with a
project, so a crafted file that crashes them or does worse is a security bug.

Please report one privately with GitHub's **Report a vulnerability** button (Security tab > Advisories), not in a
public issue. Include the file or steps that trigger it and the plug-in's version, host and OS.

Fixes go into the next release; only the latest release is supported.

Every release lists its files in `SHA256SUMS.txt`, and public releases carry GitHub build provenance attestations
(`gh attestation verify <file> --repo MaymiPR/Orrery`). The release notes say whether the Windows and macOS
files are code-signed; check an unsigned download against the checksums before running it.
