#!/usr/bin/env python3
"""
CSV to Kafka Streamer

A Python script that reads any CSV file and streams it to Confluent Kafka as JSON messages.
Each row becomes a JSON message where column names are keys and row values are the actual values.
"""

import csv
import json
import logging
import sys
import os
from typing import Dict, Any, Optional
from confluent_kafka import Producer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
import argparse


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
        # Create admin client
        admin_client = AdminClient(config)
        
        # Check if topic exists
        metadata = admin_client.list_topics(timeout=10)
        if topic in metadata.topics:
            logging.info(f"Topic '{topic}' already exists")
            return True
        
        # Create topic
        new_topic = NewTopic(topic, num_partitions=1, replication_factor=1)
        futures = admin_client.create_topics([new_topic])
        
        # Wait for topic creation
        for topic_name, future in futures.items():
            try:
                future.result()  # The result itself is None
                logging.info(f"Topic '{topic_name}' created successfully")
                return True
            except Exception as e:
                logging.error(f"Failed to create topic '{topic_name}': {str(e)}")
                return False
                
    except Exception as e:
        logging.warning(f"Could not create topic '{topic}': {str(e)}. Proceeding anyway...")
        return True  # Proceed even if we can't create topic (it might exist)


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


def stream_csv_to_kafka(csv_file: str, topic: str, config: Dict[str, str], 
                       batch_size: int = 1000, delimiter: str = ',') -> None:
    """
    Stream CSV file to Kafka topic as JSON messages
    
    Args:
        csv_file: Path to the CSV file
        topic: Kafka topic name
        config: Kafka configuration
        batch_size: Number of messages to batch before flushing
        delimiter: CSV delimiter character
        
    Raises:
        Exception: If streaming fails
    """
    # Create producer with error handling
    try:
        producer = Producer(config)
        logging.info("Kafka producer created successfully")
    except Exception as e:
        raise Exception(f"Failed to create Kafka producer: {str(e)}")
    
    messages_sent = 0
    messages_failed = 0
    
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
            logging.info(f"Starting to stream CSV to topic '{topic}'")
            
            # Process each row
            for row_num, row in enumerate(reader, 1):
                try:
                    # Clean the row data - remove None values and strip whitespace
                    cleaned_row = {}
                    for key, value in row.items():
                        if key is not None:  # Skip None keys
                            cleaned_key = str(key).strip()
                            cleaned_value = str(value).strip() if value is not None else ""
                            cleaned_row[cleaned_key] = cleaned_value
                    
                    # Convert row to JSON
                    json_message = json.dumps(cleaned_row, ensure_ascii=False)
                    
                    # Create message key (you can customize this logic)
                    message_key = f"row_{row_num}"
                    
                    # Send message to Kafka
                    producer.produce(
                        topic=topic,
                        key=message_key,
                        value=json_message,
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


def main():
    """Main function to orchestrate the CSV to Kafka streaming"""
    parser = argparse.ArgumentParser(description='Stream CSV file to Confluent Kafka as JSON messages')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('topic', help='Kafka topic name')
    parser.add_argument('--config', default='client.properties', help='Kafka configuration file (default: client.properties)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for flushing messages (default: 1000)')
    parser.add_argument('--delimiter', default=',', help='CSV delimiter (default: ,)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       help='Logging level (default: INFO)')
    parser.add_argument('--create-topic', action='store_true', help='Create topic if it does not exist')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    try:
        # Validate inputs
        validate_csv_file(args.csv_file)
        
        # Read Kafka configuration
        logging.info(f"Reading configuration from '{args.config}'")
        config = read_config(args.config)
        
        # Create topic if requested
        # if args.create_topic:
        #     create_topic_if_not_exists(config, args.topic)
        
        # Stream CSV to Kafka
        logging.info(f"Starting CSV to Kafka streaming process")
        stream_csv_to_kafka(
            csv_file=args.csv_file,
            topic=args.topic,
            config=config,
            batch_size=args.batch_size,
            delimiter=args.delimiter
        )
        
        logging.info("CSV to Kafka streaming completed successfully")
        
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()