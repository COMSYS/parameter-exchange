#!/usr/bin/env bash
REPS=10

echo "Excute from src/"

echo "Client Random ID 1"
git checkout -f lib/config.py
time python3 -m eval.client -r $REPS -o butthead_psi_vs_bloom2 --random --psi -m relOffset-0.3
echo "Client IKV"
git checkout -f lib/config.py
time python3 -m eval.client -r $REPS -o butthead_client_ikv1 --ikv --psi
echo "Client WZL1"
git checkout -f lib/config.py
time python3 -m eval.client -r $REPS -o butthead_client_wzl1 --wzl1 --psi
echo "Client WZL2"
git checkout -f lib/config.py
time python3 -m eval.client -r $REPS -o butthead_client_wzl2 --wzl2 --psi
# Done
#echo "Baseline76 OT Eval"
#git checkout -f lib/config.py
#time python3 -m eval.ot_eval -r $REPS -t 0 --baseline -o butthead_ot_baseline76
#
# Done
#echo "Baseline128 OT Eval"
#git checkout -f lib/config.py
#time python3 -m eval.ot_eval -r $REPS -t 0 -o butthead_ot_baseline128
#
# Done
#echo "TLS OT Eval"
#git checkout -f lib/config.py
#time python3 -m eval.ot_eval -r $REPS -t 1 -o butthead_ot_tls
#
# Done
#
#echo "Client Random ID 1"
#git checkout -f lib/config.py
#time python3 -m eval.client -r 1 -o butthead_psi_vs_bloom --random --psi -m relOffset-0.3
#

#echo "Client IKV"
#git checkout -f lib/config.py
#time python3 -m eval.client -r $REPS -o butthead_client_ikv1 --ikv

# Done
#echo "Bandwidth PSI Eval"
#git checkout -f lib/config.py
#time python3 -m eval.psi_eval -r $REPS -t 0 -b -o butthead_psi_bandwidth

#Done
#echo "Repeat RR16 Eval"
#git checkout -f lib/config.py
#time python3 -m eval.psi_eval -r $REPS -t 0 -m -o butthead_psi_rr16

# Done
#echo "Repeat Client IKV"
#git checkout -f lib/config.py
#time python3 -m eval.client -r $REPS -o butthead_client_ikv2 --ikv

# Done
#echo "Client Random ID 2"
#git checkout -f lib/config.py
#time python3 -m eval.client -r $REPS -o butthead_bloom --random -m relOffset-0.5

# Done
#echo "Repeat PSI Setsize Eval"
#git checkout -f lib/config.py
#time python3 -m eval.psi_eval -r $REPS -t 0 -o butthead_psi_setsize2

# Done
#echo "Data Provider WZL"
#git checkout -f lib/config.py
#time python3 -m eval.data_provider -r $REPS -o butthead_provider_wzl --wzl

#echo "Data Provider IKV2"
#git checkout -f lib/config.py
#time python3 -m eval.data_provider -r $REPS -o butthead_provider_ikv2 --ikv2
#
#echo "Data Provider Random ID 1"
#git checkout -f lib/config.py
#time python3 -m eval.data_provider -r $REPS --uploads -o butthead_provider_uploads
#
#echo "Data Provider Random ID 1"
#git checkout -f lib/config.py
#time python3 -m eval.data_provider -r $REPS --rec_len -o butthead_provider_record_length

# Done echo "Baseline PSI Eval"
#git checkout -f lib/config.py
#time python3 -m eval.psi_eval -r $REPS -t 0 -o butthead_psi_baseline

# Done echo "TLS PSI Eval"
#git checkout -f lib/config.py
#time python3 -m eval.psi_eval -r $REPS -t 1 -o butthead_psi_tls

#Done echo "Malicious OT Eval"
#git checkout -f lib/config.py
#time python3 -m eval.ot_eval -r $REPS -t 0 -m -o butthead_ot_malicious
