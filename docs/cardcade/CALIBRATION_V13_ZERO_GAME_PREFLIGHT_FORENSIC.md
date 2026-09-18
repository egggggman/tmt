# V13 zero-game preflight forensic

## Classification

`PREFLIGHT_FAILURE — launcher_packet_sidecar_path_construction`

Run `CALIBRATION_V1_20260917T235000Z_v13b590a28` is permanently consumed. It started zero Protocol V1 members, games, executions, and seeds. The stopped-run directory is preserved unchanged.

## Exact terminal evidence

```
Traceback (most recent call last):
  File "...\\CALIBRATION_V1_20260917T235000Z_v13b590a28\\launcher.py", line 10, in <module>
    assert hashlib.sha256(blob).hexdigest().upper()==Path(ROOT/PACKET+'.sha256').read_text('ascii').split()[0]
                                                          ~~~~~~~~~~~^~~~~~~~~~
TypeError: unsupported operand type(s) for +: 'WindowsPath' and 'str'
```

The failing construction is line 10 of the generated launcher. It evaluates `ROOT / PACKET` first, producing a `WindowsPath`, then attempts `+ '.sha256'`; it therefore fails before imports of `calibration_runner` or `calibration_executor` and before `execute_protocol`.

## Identity and origin

- Generated stopped-run launcher SHA-256: `60936CA6899076BB078BA5E2E6CB82D571EC6CC8A548513312A19D8E30437A9C`
- Authorized committed V13 launcher SHA-256: `308184F5FBE9BF8D252B7BBFA23F30A4594408CE8C28BFA269E45A6E61B1853A`
- The identities differ. The faulty bytes were generated downstream in the one-off runtime wrapper, not from the committed V13 release launcher or its template.

## Scope search and deterministic reproduction

A search of the committed V13 launcher and relevant launcher path found no equivalent `Path + str` packet-sidecar expression. Existing sidecar construction in repository scripts uses safe string conversion or `with_suffix` forms. Evaluating only the offending `Path(ROOT / PACKET + '.sha256')` construction deterministically raises the same `TypeError`; it neither imports the Protocol V1 runner nor creates a member, game, execution, or seed.

No repair, retry, resume, runtime change, protocol change, seed change, or balance analysis occurred.