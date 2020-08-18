#!/usr/bin/env bash
REPS=10
NUM=12  # Number of Evals + 1

echo "Excute from src/"

for (( i = 1; i < $NUM; i++ )); do
    echo "Starting ID ${i}"
    time python3 -m eval.metric_eval -r $REPS -o "metric_id${i}" --id${i}
done
