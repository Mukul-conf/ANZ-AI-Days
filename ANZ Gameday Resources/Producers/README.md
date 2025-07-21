# CSV to Kafka Avro Producer

A dynamic, config-driven Kafka producer that reads CSV files and publishes them to Kafka topics in Avro format.

## Project Structure

```
/Producers/
├── producer.py          # Main producer script
├── client.properties    # Kafka configuration
├── schemas.avsc         # Avro schemas for all topics
└── README.md           # This file
```


## Prerequisites

```bash
pip install confluent-kafka
```

## Topic and Schema Management

### Automatic Topic Creation
The producer automatically creates topics if they don't exist with these default settings:
- **Partitions**: 3 (suitable for most use cases)
- **Replication Factor**: 3 

### Manual Topic Creation (Optional)
If you prefer to create topics manually through UI , you can:

1. **Using Confluent Cloud UI**:
   - Navigate to Topics section
   - Click "Create topic"
   - Use CSV filename as topic name (e.g., `user_behaviour`)
   - Set partitions as needed


### Schema Registry Integration
The producer handles Schema Registry automatically:
- **Auto Registration**: Registers schemas from `schemas.avsc` file
- **Schema Validation**: Checks existing schemas for compatibility
- **Subject Naming**: Uses `{topic-name}-value` format
- **Version Management**: Handles schema evolution

## Configuration

### 1. Update `client.properties`

```properties
# Confluent Cloud Configuration
bootstrap.servers=your-cluster.confluent.cloud:9092
security.protocol=SASL_SSL
sasl.mechanisms=PLAIN
sasl.username=your-api-key
sasl.password=your-api-secret

# Schema Registry Configuration
schema.registry.url=https://your-schema-registry.confluent.cloud
schema.registry.password=sr-api-key:sr-api-secret

```

### 2. Add Avro Schemas

For each new CSV file, add its schema to `schemas.avsc`:

```json
{
  "your_topic_name": {
    "type": "record",
    "name": "YourRecordName",
    "namespace": "com.example.streaming",
    "fields": [
      {
        "name": "field_name",
        "type": "string"
      }
    ]
  }
}
```

## Usage

### Basic Usage

```bash
# From the data_producer directory
python producer.py -f ../Sample\ data/
```

### With Custom Config

```bash
python producer.py -f /path/to/csv/folder -c my_config.properties -s my_schemas.avsc
```

### Command Line Arguments

- `-f, --folder`: Path to folder containing CSV files (required)
- `-c, --config`: Path to configuration file (default: client.properties)
- `-s, --schema`: Path to schema file (default: schemas.avsc)

## How It Works

1. **File Discovery**: Scans the specified folder for `.csv` files
2. **Topic Mapping**: Uses filename (without .csv) as topic name
3. **Schema Lookup**: Matches topic name with schema in `schemas.avsc`
4. **Data Processing**: Reads CSV and converts to Avro format
5. **Publishing**: Sends records to corresponding Kafka topic

## Schema Data Types

The producer supports these Avro data types:

- `string`: Text data
- `int`: 32-bit integers
- `long`: 64-bit integers  
- `float`: 32-bit floating point
- `double`: 64-bit floating point
- `boolean`: true/false values
- `["null", "type"]`: Optional fields

## Adding New CSV Files

1. Place your CSV file in the data folder
2. Add corresponding schema to `schemas.avsc` with the same name as your CSV file (without .csv extension)
3. Run the producer

Example: For `new_data.csv`, add schema with key `"new_data"` in `schemas.avsc`

## Error Handling

- Invalid records are skipped with error logging
- Missing schemas result in topic being skipped
- Network errors are reported but don't stop processing

## Example Output

```
Producing records from user_behaviour.csv to topic user_behaviour
Record 12345 delivered to user_behaviour [0] at offset 42
Produced 9 records to topic user_behaviour
Flushing remaining messages...
All messages flushed successfully!
```

## Troubleshooting

### Common Issues

1. **Schema Registry Connection**: 
   - Ensure Schema Registry is running and accessible
   - Check authentication credentials in `client.properties`
   - Verify URL format (no trailing slashes)

2. **Kafka Connection**: 
   - Verify bootstrap.servers in client.properties
   - Check network connectivity to Kafka cluster
   - Ensure security protocol matches cluster configuration

3. **Authentication Errors**: 
   - Double-check SASL credentials for Kafka
   - Ensure credentials have proper permissions

4. **Schema Issues**: 
   - Ensure CSV headers match schema field names exactly
   - Check data types in schema match CSV data
   - Verify schema syntax in `schemas.avsc`

5. **Topic Creation Failures**: 
   - Check if you have topic creation permissions
   - Verify cluster has sufficient resources
   - Manual topic creation may be required in some environments

### Error Messages

- `"Expecting value: line 1 column 1"`: Empty or corrupted `schemas.avsc` file
- `"Schema not found for topic"`: Missing schema definition in `schemas.avsc`
- `"Delivery failed"`: Network issues or authentication problems
- `"Too many errors"`: Data format issues in CSV file

### Getting Help

For Confluent Cloud specific issues:
- Check [Confluent Cloud Documentation](https://docs.confluent.io/cloud/)
- Verify cluster status in Confluent Cloud UI
- Review API access.
