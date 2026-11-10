# Dedicated Windows Diagnostic Runner Security Design

## Purpose and status

This is a deployment proposal for the future single-host Cardcade diagnostic launcher. It does not provision an account or key, change NTFS ACLs, issue permits, or authorize execution.

The current shared development workspace is not an acceptable runner boundary: its repository root and shared claim directory inherit `NT AUTHORITY\Authenticated Users: Modify`, and the runner-specific ACLs and authorization-file locations have not been established.

**Deployment recommendation: BLOCKED** until the designated host passes the acceptance checks below and revocation is enforceable at dispatch time.

## Host and identity

- Use one dedicated, managed Windows host or VM with a documented owner and change-control record. Do not run the diagnostic from `C:\projects\tmt` or another shared developer checkout.
- Run as a dedicated non-administrator service identity, preferably a domain gMSA where domain policy supports it; otherwise use a managed local standard account with rotated credentials held by the Windows credential manager. Deny interactive, RDP, and ordinary network logon. Grant only the service/batch logon rights required by the chosen service wrapper.
- Keep unrelated developer, interactive user, sandbox, and general authenticated-user groups out of all writable paths. Administrators and SYSTEM retain recovery access. Enable Windows security auditing for service logon, ACL changes, permit access, and diagnostic output access.
- Run one worker at a time under a Windows service or controlled task with automatic retries and restart-on-failure disabled. Restrict child processes with a Job Object or equivalent service policy. Restrict outbound networking to the minimum required for approved source retrieval and central audit; gameplay itself must not receive an arbitrary shell or network capability.

## Filesystem layout and least privilege

Use a dedicated local NTFS volume or a dedicated, non-shared directory tree such as `D:\CardcadeDiagnostic\`. Do not use a network share, roaming profile, developer temp folder, or a source checkout writable by the service identity.

| Path | SYSTEM / Administrators | Runner service identity | HQ approver / evidence custodian |
| --- | --- | --- | --- |
| `source\<approved-sha>\` | Full control | Read, execute, traverse only | Provision/update during reviewed deployment |
| `runtime\<lock-digest>\` | Full control | Read, execute only | Build and verify from `uv.lock`; no runtime package installation |
| `approvals\source\` | Full control | Read only | Create signed exact-SHA approval |
| `approvals\runs\` | Full control | Read only | Create unique signed run authorization |
| `claims\` | Full control | Create new claim files and read claims; no delete/rename | Read/audit; deletion only through documented administrative recovery |
| `runs\<authorization-id>\` | Full control | Create once and write during that invocation | Read after completion; copy to protected evidence archive |
| `archive\` | Full control | No write after evidence is sealed | Append/retain under evidence-custodian workflow |

Use explicit, non-inherited ACLs at the root and each boundary. Grant no write access to `Users`, `Authenticated Users`, developer accounts, or sandbox groups. The service identity must not be able to change ACLs, replace executables, modify the approved source/runtime, delete prior claims, or overwrite prior evidence. Deny claim deletion and rename to the runner; verify the effective access with access-check tooling and a negative test under the actual service token.

The runner needs write access only to its new claim and active run directory. After successful persistence, a privileged sealing step should remove service write access to that run and copy its manifest and files into an append-only or retention-locked evidence archive. A later invocation must create a new unique output directory; it must never reopen an old run directory.

## Source, dependency, and credential custody

- Pin the implementation by exact reviewed source SHA and frozen-input hashes. Materialize the source in an administrator-controlled, read-only tree; verify its Git commit and hashes before service startup.
- Build the runtime from the committed lock file in a controlled staging process. The runner receives a read-only environment and cannot install or update packages while executing.
- Keep the Ed25519 private signing key outside the repository and runner. Prefer an offline HSM or approved signing service with named custodians, dual approval, immutable issuance audit, and tested backup/recovery. Do not copy private key material to the runner.
- The reviewed public key is code/configuration trust material and must be provisioned through a reviewed source change. The present candidate's `TRUSTED_HQ_AUTHORIZATION_KEYS` is empty and rejects all real permits.
- Keep source approval and run authorization as separate signed documents. The run permit binds the exact implementation SHA, all frozen hashes, match specification, seed/orientation, unique authorization ID, and issue/expiry times. Any code, trust registry, lock, or input change requires new exact-source approval and a newly signed run permit.

## Revocation and one-use claims

The launcher has durable local one-use claims, but no online revocation lookup or expiry mechanism. A signed permit copied before a local file is removed could still be presented. Therefore the deployed flow must not rely on “delete the permit file” as sufficient revocation.

Before production deployment, add or approve an authoritative revocation check that the launcher performs immediately before atomically claiming and dispatching an authorization. The check must bind the authorization ID and exact source SHA, fail closed when unavailable, and define race behavior with the one-use claim. Revocation state must be signed, auditable, and protected from runner modification. An emergency operator can disable the service and isolate the host immediately; this prevents new dispatches but does not undo a process that has already passed the final authorization check.

Claims are created on local NTFS before executor invocation and remain consumed after exceptions, incomplete evidence, or crashes. Preserve the claim and run folder after any uncertain failure. Do not delete a claim, reuse an authorization ID, or automatically retry. Reauthorization requires incident review, proof that no execution occurred where possible, and a fresh unique HQ permit. Backups must not restore a pre-claim view that permits replay; recovery must reconcile claims against the signed issuance/consumption audit.

## Evidence retention and crash response

- Allocate an output directory only after signature, source, input, revocation, and one-use checks pass.
- Persist the captured snapshot, presence ledger, event/priority trace, raw reconciliation, trusted expected reconciliation, status, errors, and artifact hash manifest. A reconciliation or persistence failure remains BLOCKED with nonzero exit.
- On crash or interrupted I/O, quarantine the incomplete run directory and preserve its authorization claim. Do not mark it successful or rerun it. An operator reviews event, claim, and filesystem state and records an incident disposition.
- Test abrupt process termination at each boundary: before claim, after claim, during executor invocation, during snapshot persistence, during reconciliation, and during final manifest write. Validate behavior after reboot and backup restoration on the actual host.

## Deployment acceptance checklist

1. A designated host, service identity, owner, service wrapper, and recovery operator are named.
2. ACL inspection confirms no general-user or developer write access to source, approvals, claims, runtime, output, or archive.
3. The service cannot edit source/runtime, delete an existing claim, overwrite a prior run, or access an unapproved permit.
4. Parallel processes and service restarts cannot reuse one authorization; crash tests prove claims remain consumed after reboot.
5. Signed revocation is checked at dispatch and races with claim creation are tested.
6. Synthetic-only end-to-end launcher tests pass under the service identity with locked dependencies and no gameplay.
7. Private-key custody, two-person issuance, rotation/revocation, backups, incident response, and audit retention are approved by HQ.

Until these items are completed, the source candidate may proceed through HQ's controlled integration review, but the runner, production trust anchor, real authorization documents, and gameplay remain blocked.
