# Eval Results

This directory contains only complete measurements that have been executed correctly and may be used for the evaluation.

## PSI

**Honest-But-Curious:** KKRT16

**Malicious Secure:** RR16

**SETSIZE**
The largest set size that succeeds on *butthead* is `70.000.000`. (Limited by RAM)

**STATSECPARAM:**
At least for a non malicious secure PSI there seems to be no influence.
However, for `statsecparam > 80` wrong results are computed !

## OT

**Honest-But-Curious:** KKRT16

**Malicious Secure:** OOS16

**Total OTs**:
With a `setSize=1.000.000` it is possible to execute 268 OTs at once (`totalOTs`).

**Set Size**:
Largest setsize that completed with `totalOTs=1` is `26.0000.000`.

**StatSecParams:**
At least for a not malicious secure OT (KKRT), the choice of the statistical security parameters has no influence on execution speed.