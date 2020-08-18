#!/usr/bin/env python3
"""This module contains functions for the theoretic TLS approximation."""
from copy import deepcopy

# Deprecated ------------------------------------------------------------------
# Handshake cost < 1s
# https://www.comsys.rwth-aachen.de/fileadmin/papers/2019/2019-hiller-lcn
# -case_for_tls_session_sharing.pdf
# According to https://tools.ietf.org/id/draft-mattsson-uta-tls-overhead-01
# .html
# AES-128-GCM (Worst Case) provides 41.5MB/s in SW
# PER_BYTE_OVERHEAD = 1. / 1000000. / 41.5
# -----------------------------------------------------------------------------

# The following values have been produces with the tls_test script
# TLSv1.2, ECDHE-RSA-AES256-GCM-SHA384, secp256r1

HANDSHAKE_COST = 0.05394  # 53.94ms
PER_BYTE_OVERHEAD = 1. / 1000000. / 567.16  # 567.16MB/s


def compute_tls_curve(baseline, sent, recv):
    """
    Compute the TLS values
    :param baseline: The baseline curve to add TLS to
    :param sent: Sent bytes [same X-Values as baseline]
    :param recv: Received bytes [same X-Values as baseline]
    :return:
    """
    tls = deepcopy(baseline)
    for x in tls:
        for i, _ in enumerate(tls[x]):
            tls[x][i] += HANDSHAKE_COST
            tls[x][i] += sent[x][i] * PER_BYTE_OVERHEAD
            tls[x][i] += recv[x][i] * PER_BYTE_OVERHEAD
    return tls
