#!/usr/bin/env python3
"""
CSV to Kafka Streamer with Avro Serialization

A Python script that reads any CSV file and streams it to Confluent Kafka as Avro messages.
Each row becomes an Avro message based on the provided schema file.
"""

import csv
import json
import logging
import sys
import os
import glob
from typing import Dict, Any, Optional, List
from confluent_kafka import Producer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
import argparse
import time
import random


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('csv_kafka_streamer.log')
        ]
    )


def read_config(config_file: str = "client.properties") -> Dict[str, str]:
    """
    Read Kafka configuration from properties file
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Dictionary containing configuration parameters
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is malformed
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file '{config_file}' not found")
    
    config = {}
    try:
        with open(config_file, 'r', encoding='utf-8') as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                # Skip empty lines and comments
                if len(line) == 0 or line.startswith('#'):
                    continue
                
                if '=' not in line:
                    logging.warning(f"Skipping malformed line {line_num}: {line}")
                    continue
                
                parameter, value = line.split('=', 1)
                config[parameter.strip()] = value.strip()
                
        logging.info(f"Successfully loaded {len(config)} configuration parameters")
        return config
        
    except Exception as e:
        raise ValueError(f"Error reading configuration file: {str(e)}")


def read_avro_schemas(schema_file: str) -> Dict[str, str]:
    """
    Read multiple Avro schemas from .avsc file
    
    Args:
        schema_file: Path to the .avsc schema file
        
    Returns:
        Dictionary mapping schema names to schema strings
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        ValueError: If schema file is malformed
    """
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file '{schema_file}' not found")
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_content = f.read()
            # Parse the JSON content
            schemas_dict = json.loads(schema_content)
            
            # Convert each schema to JSON string
            avro_schemas = {}
            for schema_name, schema_def in schemas_dict.items():
                avro_schemas[schema_name] = json.dumps(schema_def)
                
            logging.info(f"Successfully loaded {len(avro_schemas)} Avro schemas from '{schema_file}'")
            logging.info(f"Available schemas: {list(avro_schemas.keys())}")
            return avro_schemas
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in schema file '{schema_file}': {str(e)}")
    except Exception as e:
        raise ValueError(f"Error reading schema file '{schema_file}': {str(e)}")


def validate_csv_file(csv_file: str) -> None:
    """
    Validate if CSV file exists and is readable
    
    Args:
        csv_file: Path to the CSV file
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        PermissionError: If CSV file is not readable
    """
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file '{csv_file}' not found")
    
    if not os.access(csv_file, os.R_OK):
        raise PermissionError(f"CSV file '{csv_file}' is not readable")


def create_topic_if_not_exists(config: Dict[str, str], topic: str) -> bool:
    """
    Create Kafka topic if it doesn't exist
    
    Args:
        config: Kafka configuration
        topic: Topic name to create
        
    Returns:
        True if topic exists or was created successfully, False otherwise
    """
    try:
        # Create admin client config (remove schema registry configs)
        admin_config = {k: v for k, v in config.items() 
                       if not k.startswith('schema.registry')}
        
        # Create admin client
        admin_client = AdminClient(admin_config)
        
        # Check if topic exists
        metadata = admin_client.list_topics(timeout=10)
        if topic in metadata.topics:
            logging.info(f"Topic '{topic}' already exists")
            return True
        
        # Create topic with appropriate settings for Confluent Cloud
        new_topic = NewTopic(
            topic, 
            num_partitions=6,  # Good default for Confluent Cloud
            replication_factor=3  # Standard for Confluent Cloud
        )
        
        futures = admin_client.create_topics([new_topic])
        
        # Wait for topic creation
        for topic_name, future in futures.items():
            try:
                future.result(timeout=30)  # Increased timeout for cloud
                logging.info(f"Topic '{topic_name}' created successfully")
                return True
            except Exception as e:
                if "already exists" in str(e).lower():
                    logging.info(f"Topic '{topic_name}' already exists")
                    return True
                else:
                    logging.error(f"Failed to create topic '{topic_name}': {str(e)}")
                    return False
                
    except Exception as e:
        logging.error(f"Could not create topic '{topic}': {str(e)}")
        return False


def delivery_report(err: Optional[KafkaError], msg) -> None:
    """
    Delivery report callback for Kafka producer
    
    Args:
        err: Error object if delivery failed
        msg: Message object
    """
    if err is not None:
        logging.error(f"Message delivery failed: {err}")
    else:
        logging.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


def convert_csv_row_to_avro_dict(row: Dict[str, Any], schema_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert CSV row to match Avro schema types
    
    Args:
        row: CSV row as dictionary
        schema_dict: Parsed Avro schema
        
    Returns:
        Dictionary with properly typed values for Avro
    """
    avro_record = {}
    
    # Get field definitions from schema
    fields = schema_dict.get('fields', [])
    field_types = {field['name']: field['type'] for field in fields}
    
    for key, value in row.items():
        if key in field_types:
            field_type = field_types[key]
            
            # Handle union types (e.g., ["null", "string"])
            if isinstance(field_type, list):
                # Find the non-null type
                non_null_type = next((t for t in field_type if t != "null"), "string")
                field_type = non_null_type
            
            # Convert value based on Avro field type
            try:
                if field_type == "string" or field_type == "bytes":
                    avro_record[key] = str(value) if value is not None else ""
                elif field_type == "int":
                    avro_record[key] = int(float(value)) if value and str(value).strip() else 0
                elif field_type == "long":
                    avro_record[key] = int(float(value)) if value and str(value).strip() else 0
                elif field_type == "float":
                    avro_record[key] = float(value) if value and str(value).strip() else 0.0
                elif field_type == "double":
                    avro_record[key] = float(value) if value and str(value).strip() else 0.0
                elif field_type == "boolean":
                    avro_record[key] = str(value).lower() in ('true', '1', 'yes', 'on') if value else False
                else:
                    avro_record[key] = str(value) if value is not None else ""
            except (ValueError, TypeError) as e:
                logging.warning(f"Type conversion error for field '{key}' with value '{value}': {e}")
                # Set default value based on type
                if field_type in ["int", "long"]:
                    avro_record[key] = 0
                elif field_type in ["float", "double"]:
                    avro_record[key] = 0.0
                elif field_type == "boolean":
                    avro_record[key] = False
                else:
                    avro_record[key] = ""
        else:
            # Field not in schema, skip or add as string if schema allows
            logging.debug(f"Field '{key}' not found in schema, skipping")
    
    return avro_record


def get_topic_name_from_filename(csv_file: str) -> str:
    """
    Extract topic name from CSV filename
    
    Args:
        csv_file: Path to CSV file
        
    Returns:
        Topic name derived from filename
    """
    filename = os.path.basename(csv_file)
    topic_name = os.path.splitext(filename)[0]  # Remove .csv extension
    return topic_name


def stream_csv_to_kafka(csv_file: str, topic: str, config: Dict[str, str], 
                       avro_serializer: AvroSerializer, schema_dict: Dict[str, Any],
                       batch_size: int = 1000, delimiter: str = ',') -> None:
    """
    Stream CSV file to Kafka topic as Avro messages
    
    Args:
        csv_file: Path to the CSV file
        topic: Kafka topic name
        config: Kafka configuration
        avro_serializer: Configured Avro serializer
        schema_dict: Parsed Avro schema dictionary
        batch_size: Number of messages to batch before flushing
        delimiter: CSV delimiter character
        
    Raises:
        Exception: If streaming fails
    """
    # Create producer with Avro serializer
    producer_config = config.copy()
    # Remove schema registry configs from producer config
    producer_config = {k: v for k, v in producer_config.items() 
                      if not k.startswith('schema.registry')}
    
    try:
        producer = Producer(producer_config)
        logging.info("Kafka producer created successfully")
    except Exception as e:
        raise Exception(f"Failed to create Kafka producer: {str(e)}")
    
    messages_sent = 0
    messages_failed = 0
    
    # Check if this is a throttled file
    throttled_files = ["users_behaviour", "imdb_synthetic_reviews"]
    is_throttled = any(throttled_file in csv_file for throttled_file in throttled_files)
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            # Detect CSV dialect and create reader
            sample = file.read(1024)
            file.seek(0)
            sniffer = csv.Sniffer()
            
            try:
                dialect = sniffer.sniff(sample, delimiters=delimiter)
                reader = csv.DictReader(file, delimiter=dialect.delimiter)
            except csv.Error:
                # Fallback to specified delimiter
                reader = csv.DictReader(file, delimiter=delimiter)
            
            # Get column names
            fieldnames = reader.fieldnames
            if not fieldnames:
                raise ValueError("CSV file appears to be empty or has no headers")
            
            logging.info(f"CSV columns detected: {fieldnames}")
            logging.info(f"Starting to stream CSV to topic '{topic}' using Avro serialization")
            
            if is_throttled:
                logging.info(f"Throttled mode enabled for {csv_file}: 10 messages per 2 seconds")
                
                # Read all rows first for shuffling
                all_rows = list(reader)
                random.shuffle(all_rows)
                
                # Process rows with throttling
                for row_num, row in enumerate(all_rows, 1):
                    try:
                        # Clean the row data - remove None values and strip whitespace
                        cleaned_row = {}
                        for key, value in row.items():
                            if key is not None:  # Skip None keys
                                cleaned_key = str(key).strip()
                                cleaned_value = str(value).strip() if value is not None else ""
                                cleaned_row[cleaned_key] = cleaned_value
                        
                        # Convert to Avro compatible format
                        avro_record = convert_csv_row_to_avro_dict(cleaned_row, schema_dict)
                        
                        # Create message key
                        message_key = f"row_{row_num}"
                        
                        # Serialize the record using Avro
                        serialized_value = avro_serializer(
                            avro_record,
                            SerializationContext(topic, MessageField.VALUE)
                        )
                        
                        # Send message to Kafka
                        producer.produce(
                            topic=topic,
                            key=message_key,
                            value=serialized_value,
                            callback=delivery_report
                        )
                        
                        messages_sent += 1
                        
                        # Throttle: send 10 messages every 2 seconds
                        if messages_sent % 10 == 0:
                            producer.flush()
                            logging.info(f"Processed {messages_sent} messages (throttled)")
                            time.sleep(2)
                            
                    except Exception as e:
                        messages_failed += 1
                        logging.error(f"Failed to process row {row_num}: {str(e)}")
                        continue
            else:
                # Normal processing for non-throttled files
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Clean the row data - remove None values and strip whitespace
                        cleaned_row = {}
                        for key, value in row.items():
                            if key is not None:  # Skip None keys
                                cleaned_key = str(key).strip()
                                cleaned_value = str(value).strip() if value is not None else ""
                                cleaned_row[cleaned_key] = cleaned_value
                        
                        # Convert to Avro compatible format
                        avro_record = convert_csv_row_to_avro_dict(cleaned_row, schema_dict)
                        
                        # Create message key
                        message_key = f"row_{row_num}"
                        
                        # Serialize the record using Avro
                        serialized_value = avro_serializer(
                            avro_record,
                            SerializationContext(topic, MessageField.VALUE)
                        )
                        
                        # Send message to Kafka
                        producer.produce(
                            topic=topic,
                            key=message_key,
                            value=serialized_value,
                            callback=delivery_report
                        )
                        
                        messages_sent += 1
                        
                        # Flush every batch_size messages
                        if messages_sent % batch_size == 0:
                            producer.flush()
                            logging.info(f"Processed {messages_sent} messages")
                            
                    except Exception as e:
                        messages_failed += 1
                        logging.error(f"Failed to process row {row_num}: {str(e)}")
                        continue
            
            # Final flush
            producer.flush()
            
            logging.info(f"Streaming completed. Messages sent: {messages_sent}, Failed: {messages_failed}")
            
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file '{csv_file}' not found")
    except PermissionError:
        raise PermissionError(f"Permission denied reading CSV file '{csv_file}'")
    except UnicodeDecodeError as e:
        raise ValueError(f"CSV file encoding error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error streaming CSV to Kafka: {str(e)}")
    finally:
        # Ensure all messages are sent
        producer.flush()


def get_csv_files(directory: str) -> List[str]:
    """
    Get all CSV files from the specified directory
    
    Args:
        directory: Directory path containing CSV files
        
    Returns:
        List of CSV file paths
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory '{directory}' not found")
    
    if not os.path.isdir(directory):
        raise ValueError(f"'{directory}' is not a directory")
    
    csv_files = glob.glob(os.path.join(directory, "*.csv"))
    
    if not csv_files:
        raise ValueError(f"No CSV files found in directory '{directory}'")
    
    return sorted(csv_files)


def fix_avro_schema_defaults(schema_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix Avro schema to handle null defaults properly
    
    Args:
        schema_dict: Original schema dictionary
        
    Returns:
        Fixed schema dictionary with proper union types for nullable fields
    """
    if 'fields' not in schema_dict:
        return schema_dict
    
    fixed_fields = []
    for field in schema_dict['fields']:
        field_copy = field.copy()
        
        # If default is null but type is not nullable, make it nullable
        if field_copy.get('default') is None and field_copy.get('type') not in ['null', ['null']]:
            field_type = field_copy['type']
            if isinstance(field_type, str) and field_type != 'null':
                # Convert to nullable union type
                field_copy['type'] = ["null", field_type]
                logging.debug(f"Fixed field '{field['name']}': converted type '{field_type}' to nullable union")
            elif isinstance(field_type, list) and 'null' not in field_type:
                # Add null to existing union
                field_copy['type'] = ['null'] + field_type
                logging.debug(f"Fixed field '{field['name']}': added null to union type")
        
        fixed_fields.append(field_copy)
    
    schema_dict_copy = schema_dict.copy()
    schema_dict_copy['fields'] = fixed_fields
    return schema_dict_copy
def get_schema_for_topic(topic_name: str, avro_schemas: Dict[str, str]) -> tuple:
    """
    Get the appropriate schema for a given topic
    
    Args:
        topic_name: Name of the Kafka topic
        avro_schemas: Dictionary of available schemas
        
    Returns:
        Tuple of (schema_string, schema_dict) or None if not found
    """
    # Direct match
    if topic_name in avro_schemas:
        schema_str = avro_schemas[topic_name]
        schema_dict = json.loads(schema_str)
        
        # Fix schema defaults for nullable fields
        schema_dict = fix_avro_schema_defaults(schema_dict)
        
        # Convert back to string
        fixed_schema_str = json.dumps(schema_dict)
        return fixed_schema_str, schema_dict
    
    # Try partial matches for common variations
    for schema_name in avro_schemas.keys():
        if schema_name.lower() in topic_name.lower() or topic_name.lower() in schema_name.lower():
            schema_str = avro_schemas[schema_name]
            schema_dict = json.loads(schema_str)
            
            # Fix schema defaults for nullable fields
            schema_dict = fix_avro_schema_defaults(schema_dict)
            
            # Convert back to string
            fixed_schema_str = json.dumps(schema_dict)
            
            logging.info(f"Using schema '{schema_name}' for topic '{topic_name}' (partial match)")
            return fixed_schema_str, schema_dict
    
    # No matching schema found
    logging.warning(f"No matching schema found for topic '{topic_name}'")
    logging.warning(f"Available schemas: {list(avro_schemas.keys())}")
    return None, None


def main():
    """Main function to orchestrate the CSV to Kafka streaming with Avro serialization"""
    parser = argparse.ArgumentParser(description='Stream CSV files to Confluent Kafka as Avro messages')
    parser.add_argument('-f', '--folder', required=True, help='Path to the directory containing CSV files')
    parser.add_argument('-c', '--config', default='client.properties', help='Kafka configuration file (default: client.properties)')
    parser.add_argument('-s', '--schema', required=True, help='Path to the Avro schema file (.avsc)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for flushing messages (default: 1000)')
    parser.add_argument('--delimiter', default=',', help='CSV delimiter (default: ,)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       help='Logging level (default: INFO)')
    parser.add_argument('--create-topic', action='store_true', help='Create topics if they do not exist')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    try:
        # Get all CSV files from directory
        csv_files = get_csv_files(args.folder)
        logging.info(f"Found {len(csv_files)} CSV files in directory '{args.folder}'")
        
        # Read Kafka configuration
        logging.info(f"Reading configuration from '{args.config}'")
        config = read_config(args.config)
        
        # Read Avro schemas
        logging.info(f"Reading Avro schemas from '{args.schema}'")
        avro_schemas = read_avro_schemas(args.schema)
        
        # Setup Schema Registry client
        schema_registry_conf = {}
        
        # Map schema registry configuration keys
        for key, value in config.items():
            if key.startswith('schema.registry'):
                if key == 'schema.registry.url':
                    schema_registry_conf['url'] = value
                elif key == 'schema.registry.basic.auth.user.info':
                    schema_registry_conf['basic.auth.user.info'] = value
                else:
                    # Remove 'schema.registry.' prefix for other configs
                    new_key = key.replace('schema.registry.', '')
                    schema_registry_conf[new_key] = value
        
        if not schema_registry_conf:
            # If no schema registry config found, try common defaults
            schema_registry_conf = {'url': 'http://localhost:8081'}
            logging.warning("No schema registry configuration found, using default: http://localhost:8081")
        
        logging.info(f"Schema Registry configuration: {list(schema_registry_conf.keys())}")
        
        try:
            schema_registry_client = SchemaRegistryClient(schema_registry_conf)
            logging.info("Schema Registry client created successfully")
        except Exception as e:
            logging.error(f"Failed to create Schema Registry client: {str(e)}")
            raise
        
        # Separate throttled and normal files
        throttled_files = []
        normal_files = []
        throttled_names = ["users_behaviour", "imdb_synthetic_reviews"]
        
        for csv_file in csv_files:
            if any(throttled_name in csv_file for throttled_name in throttled_names):
                throttled_files.append(csv_file)
            else:
                normal_files.append(csv_file)
        
        logging.info(f"Normal files: {len(normal_files)}, Throttled files: {len(throttled_files)}")
        
        # Process normal files first
        for csv_file in normal_files:
            try:
                validate_csv_file(csv_file)
                topic_name = get_topic_name_from_filename(csv_file)
                
                # Get appropriate schema for this topic
                schema_str, schema_dict = get_schema_for_topic(topic_name, avro_schemas)
                if not schema_str:
                    logging.error(f"No schema found for topic '{topic_name}', skipping file: {csv_file}")
                    continue
                
                # Create Avro serializer for this specific schema
                try:
                    avro_serializer = AvroSerializer(
                        schema_registry_client=schema_registry_client,
                        schema_str=schema_str
                    )
                    logging.info(f"Created Avro serializer for topic '{topic_name}'")
                except Exception as e:
                    logging.error(f"Failed to create Avro serializer for topic '{topic_name}': {str(e)}")
                    continue
                
                logging.info(f"Processing file: {csv_file} -> topic: {topic_name}")
                
                # Create topic if requested
                if args.create_topic:
                    create_topic_if_not_exists(config, topic_name)
                
                # Stream CSV to Kafka with Avro serialization
                stream_csv_to_kafka(
                    csv_file=csv_file,
                    topic=topic_name,
                    config=config,
                    avro_serializer=avro_serializer,
                    schema_dict=schema_dict,
                    batch_size=args.batch_size,
                    delimiter=args.delimiter
                )
                
                logging.info(f"Completed processing: {csv_file}")
                
            except Exception as e:
                logging.error(f"Failed to process {csv_file}: {str(e)}")
                continue
        
        # Process throttled files in parallel after normal files
        if throttled_files:
            import threading
            
            def process_throttled_file(csv_file):
                """Process a single throttled file in a separate thread"""
                try:
                    validate_csv_file(csv_file)
                    topic_name = get_topic_name_from_filename(csv_file)
                    
                    # Get appropriate schema for this topic
                    schema_str, schema_dict = get_schema_for_topic(topic_name, avro_schemas)
                    if not schema_str:
                        logging.error(f"No schema found for topic '{topic_name}', skipping file: {csv_file}")
                        return
                    
                    # Create Avro serializer for this specific schema
                    try:
                        avro_serializer = AvroSerializer(
                            schema_registry_client=schema_registry_client,
                            schema_str=schema_str
                        )
                        logging.info(f"Created Avro serializer for topic '{topic_name}' (throttled)")
                    except Exception as e:
                        logging.error(f"Failed to create Avro serializer for topic '{topic_name}': {str(e)}")
                        return
                    
                    logging.info(f"Processing throttled file: {csv_file} -> topic: {topic_name}")
                    
                    # Create topic if requested
                    if args.create_topic:
                        create_topic_if_not_exists(config, topic_name)
                    
                    # Stream CSV to Kafka with Avro serialization (with throttling built into the function)
                    stream_csv_to_kafka(
                        csv_file=csv_file,
                        topic=topic_name,
                        config=config,
                        avro_serializer=avro_serializer,
                        schema_dict=schema_dict,
                        batch_size=args.batch_size,
                        delimiter=args.delimiter
                    )
                    
                    logging.info(f"Completed processing throttled file: {csv_file}")
                    
                except Exception as e:
                    logging.error(f"Failed to process throttled file {csv_file}: {str(e)}")
            
            # Create and start threads for throttled files
            threads = []
            for csv_file in throttled_files:
                thread = threading.Thread(target=process_throttled_file, args=(csv_file,))
                threads.append(thread)
                thread.start()
                logging.info(f"Started parallel processing thread for: {csv_file}")
            
            # Wait for all throttled file threads to complete
            for thread in threads:
                thread.join()
                
            logging.info("All throttled files processing completed")
        
        logging.info("All CSV files processing completed successfully")
        
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
