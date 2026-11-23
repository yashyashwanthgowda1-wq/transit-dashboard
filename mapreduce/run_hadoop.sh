#!/bin/bash
# Runs all MapReduce jobs on a real Hadoop cluster (Hadoop Streaming).
# Usage: bash mapreduce/run_hadoop.sh data/transit_data.csv
set -e

INPUT_FILE=${1:-data/transit_data.csv}
HDFS_IN=/transit/input
HDFS_OUT=/transit/output
LOCAL_OUT=output

# Find the streaming jar (path differs between Hadoop versions)
STREAMING_JAR=$(ls $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar | head -1)

# 1. Upload data to HDFS
hdfs dfs -mkdir -p $HDFS_IN
hdfs dfs -put -f "$INPUT_FILE" $HDFS_IN/

# 2. Run every job
JOBS="hourly:sum route:sum revenue:sum stop:sum day:sum daily:sum delay:avg"
mkdir -p $LOCAL_OUT

for pair in $JOBS; do
  JOB=${pair%%:*}
  MODE=${pair##*:}
  echo "=== Running job: $JOB ($MODE) ==="
  hdfs dfs -rm -r -f $HDFS_OUT/$JOB

  hadoop jar $STREAMING_JAR \
    -files mapreduce/mapper.py,mapreduce/reducer.py \
    -mapper "python3 mapper.py $JOB" \
    -reducer "python3 reducer.py $MODE" \
    -input $HDFS_IN \
    -output $HDFS_OUT/$JOB

  # 3. Copy result back so the backend can read it
  hdfs dfs -cat $HDFS_OUT/$JOB/part-* > $LOCAL_OUT/$JOB.txt
done

echo "All jobs done. Results are in $LOCAL_OUT/"
