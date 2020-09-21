# Evaluations

## Bloom Filter Eval

**ID**|**Name**|**Rounds**|**Capacity**|**Error Rate**|**# Inserted Values**|**# Queries Values**|**Filename**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
1 **Done**|Capacity|10|0 - 1.000.000.000 by 100.000.000|10^-20|Full|100.000.000|`butthead_bloom_cap`
2 **Done**|FP Rate|10|100.000.000|10^-1 --> 10^-20|Full|100.000.000|`butthead_bloom_fp`
3 **Done**|Insert|10|100.000.000|10^-20|range(0, 1000000001, 100000000)|0|`butthead_bloom_insert`
4 **Done**|Query|10|100.000.000|10^-20|Full|range(100000000, 1000000001, 100000000)|`butthead_bloom_query`
5 **Done**|Fixed Insert|10|range(0, 1000000001, 100000000)|10^-20|100000000|0|`butthead_bloom_cap_fixed_insert`

## OT Eval

**Threads:** 1 for all

**Statistical Security Parameters (STATSECPARAM):** 40 for all

**ID**|**Name**|**SETSIZE**|**# OTs**|**Rounds**|**TLS**|**MAL SECURE**|**Latency varied?**|**Bandwidth varied?**|**INPUT BIT COUNT**|**Filename**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
1 **Done**|Set Size Dependence|1-13.000.000 By 1.000.000|10|10|False|False|No|No|128|`butthead_setsize`
2 **Done**|Total OT Dependence|2^20|10-200 by 10|10|False|False|No|No|128|`butthead_numOTs`
3 **Done**|TLS Influence|2^20|10-100 by 10|10|True|False|No|No|128|`butthead_ot_tls`
4 **Done**|MAL-SEC Influence|2^20|10-100 by 10|10|False|True|No|No|76|`butthead_ot_malicious`
5 **Done**|Latency Influence|2^20|1 + 20-100 by 20|10|False|False|0ms-300ms by 50ms|No|128|`butthead_latency`
6 **Done**|Bandwidth Influence|2^20|1 + 20-100 by 20|10|False|False|No|[6,50,100] Mbit|128|`butthead_bandwidth`
7 **Done**|Bandwidth Influence|2^20|1 + 20-100 by 20|10|False|False|No|[6,50,100] Mbit|128|`butthead_ot_bandwidth_async`
8 **Done**|Baseline128|2^20|10-100 by 10|10|False|False|No|No|128|`butthead_ot_baseline128`
9 **Done**|Baseline76|2^20|10-100 by 10|10|False|False|No|No|128|`butthead_ot_baseline76`

## PSI Eval

**ID**|**SETSIZE**|**Rounds**|**TLS**|**SCHEME**|**STATSECPARAM**|**THREADS**|**Latency Varied**|**Bandwidth Varied**|**Filename**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
1 **Done**|1-20.000.000 By 1.000.000 + Power2|10|False|KKRT16|40|1|No|No|`butthead_psi_setsize`
2 **Done**|100'000-1'000'000 By 100'000|10|True|KKRT16|40|1|No|No|`butthead_psi_tls`
3 **Done**|100'000-1'000'000 By 100'000|10|False|RR16|40|1|No|No|`butthead_psi_rr16`
6 **Done**|100'000-1'000'000 By 100'000|10|False|RR17|40|1|No|No|`butthead_psi_rr17`
3 **Done**|100'000-1'000'000 By 100'000|10|False|KKRT16|40|1|No|No|`butthead_psi_baseline`
4 **Done**|2.000.000-10.000.000 by 2.000.000 + Power2|10|False|KKRT16|40|1|0ms-300ms by 50ms|No|`butthead_psi_latency`
5 **Done**|100'000-1'000'000 By 100'000|10|False|KKRT16|40|1|No|[6,50,100] Mbit|`butthead_psi_bandwidth`

## Metric Eval

**ID**|**State**|**Rounds**|**Metric**|**Offset**|**Positive Only**|**Record Len**|**IDLen**|**Rounding**|**Filename**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
1|**Done**|10|rel. Offset|1% - 50%|False|100|10|3 (for all X)|`metric_id1`
2|**Done**|10|rel. Offset|1% - 50%|True|100|10|3 (for all X)|`metric_id2`
3|**Done**|10|rel. Offset|10%|False|10-1000|10|3 (for all X)|`metric_id3`
4|**Done**|10|rel. Offset|10%|False|100|1-100|3 (for all X)|`metric_id4`
5|**Done**|10|rel. Offset|10%|False|100|10|1-10 (for all X)|`metric_id5`
6|**Done**|10|rel. Offset|1-20%|False|28|21|2 (for all X)|`metric_ikv_id6`
7|**Done**|10|rel. Offset|10%|False|28|21|1-10 (for all X)|`metric_ikv_id7`
8|**Done**|10|rel. Offset|10%|False|28|1-21|2 (for all X)|`metric_ikv_id8`
9|**Done**|10|rel. Offset|1-20%|False|19|17|2 (for all Floats, 0 for Ints)|`metric_wzl_id9`
10|**Done**|10|rel. Offset|10%|False|19|17|1-10 (for all Floats, 0 for Ints)|`metric_wzl_id10`
11|**Done**|10|rel. Offset|10%|False|19|1-17|2 (for all Floats, 0 for Ints)|`metric_wzl_id11`
## Client Application Eval

### Random Data

**ID**|**Rounds**|**# Matches**|**PSI/Bloom Mode**|**Metric**|**Record Len**|**ID Len**|**Rounding**|**# Candidates**|**Filename**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
1 **Done**|10|range(0, 1001, 100)|Bloom&PSI|RelOffset-0.3|100|10|3 (for all X)|283500|`butthead_psi_vs_bloom`
2 **Done**|10|range(0, 1001, 100)|Bloom|RelOffset-0.5|100|10|3 (for all X)|29393280|`butthead_client_bloom`

### IKV Data

**Record & ID Length follow from data set.**

**Metric:** Choose so that there are a few matches, but not all.

**ID**|**Rounds**|**# Matches**|**PSI/Bloom Mode**|**Metric**|**Record Len**|**ID Len**|**Rounding**|**# Candidates**|**Filename**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
3 **Done**|10|See Metric|Bloom&PSI|RelOffset-2|28|21|2 (for all X)|995328|`butthead_client_ikv1`
4 **Done**|10|See Metric|Bloom|RelOffset-2.5|28|21|2 (for all X)|143327232|`butthead_client_ikv2`
5 **Done**|10|See Metric|Bloom|RelOffset-3|28|21|2 (for all X)|2548039680|`butthead_client_ikv3`

### WZL Data

**Record & ID Length follow from data set.**


**ID**|**Rounds**|**# Matches**|**PSI/Bloom Mode**|**Metric**|**Record Len**|**ID Len**|**Rounding**|**# Candidates**|**Filename**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
6 **Done**|10|See Metric|Bloom&PSI|MT-Material|19|17|3 for numbers, 0 rest|11|`butthead_client_wzl1`
7 **Done**|10|See Metric|Bloom&PSI|MT-Diameter|19|17|3 for numbers, 0 rest|701|`butthead_client_wzl2`

## Data Provider Eval

### Upload Random Data

**ID**|**Rounds**|**# Uploads**|**Record Len**|**Rounding**|**Filename**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
1 **Done**|10|range(0, 1001,100)|100|3 (for all X)|`butthead_provider_uploads`
2 **Done**|10|100|range(0, 1001,100)|3 (for all X)|`butthead_provider_record_length`

### Upload all Data of IKV (10 Reps)

**ID**|**Rounds**|**# Uploads**|**Record Len**|**ID Len**|**Rounding**|Choice|**Filename**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
3a **Done**|10|(**4620**) IKV Upload all|28|21|2 (for all X)|Random choice|`butthead_provider_ikv`
3b **Done**|10|(**4620**) IKV Upload all|28|21|2 (for all X)|Non Random|`butthead_provider_ikv2`

### Upload all Data of WZL (10 Reps)

**ID**|**Rounds**|**# Uploads**|**Record Len**|**ID Len**|**Rounding**|**Filename**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
4 **Done**|10|(**60**) Upload all|19|17|3 for numbers, 0 rest|`butthead_provider_wzl`
