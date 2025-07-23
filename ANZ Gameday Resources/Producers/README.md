# CSV to Kafka Streamer

A Python script that streams CSV files to Confluent Kafka topics using Avro serialization.

## Prerequisites

```bash
pip install confluent-kafka fastavro
```

## Configuration

Update `client.properties` with your Confluent Cloud credentials:

```properties
# Kafka Configuration
bootstrap.servers=your-cluster.confluent.cloud:9092
security.protocol=SASL_SSL
sasl.mechanisms=PLAIN
sasl.username=YOUR_API_KEY
sasl.password=YOUR_API_SECRET

# Schema Registry Configuration
schema.registry.url=https://your-schema-registry.confluent.cloud
schema.registry.basic.auth.user.info=SR_API_KEY:SR_API_SECRET
```

## Usage

```bash
python csv_kafka_streamer.py -f csv_data/ -c client.properties -s schemas.avsc --create-topic
```

## Command Line Options

| Flag | Description | Default | Required |
|------|-------------|---------|----------|
| `-f, --folder` | Directory containing CSV files | - | ✅ |
| `-c, --config` | Kafka configuration file | `client.properties` | ✅ |
| `-s, --schema` | Avro schema file | - | ✅ |
| `--create-topic` | Auto-create topics if they don't exist | Off | Recommended |
| `--batch-size` | Messages per batch | 1000 | ❌ |
| `--delimiter` | CSV delimiter | `,` | ❌ |
| `--log-level` | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO | ❌ |

## Processing Behavior

- **Normal files**: Streamed at full speed
- **Throttled files** (`users_behaviour.csv`, `imdb_synthetic_reviews.csv`): 10 messages per 2 seconds, processed in parallel

## Examples

**Basic run:**
```bash
python csv_kafka_streamer.py -f csv_data/ -c client.properties -s schemas.avsc --create-topic
```

**With custom batch size:**
```bash
python csv_kafka_streamer.py -f csv_data/ -c client.properties -s schemas.avsc --create-topic --batch-size 500
```

**Debug mode:**
```bash
python csv_kafka_streamer.py -f csv_data/ -c client.properties -s schemas.avsc --create-topic --log-level DEBUG
```

## Troubleshooting

- **"UNKNOWN_TOPIC_OR_PART"**: Add `--create-topic` flag
- **Schema Registry errors**: Verify credentials in `client.properties`
- **Detailed logs**: Check `csv_kafka_streamer.log` file
