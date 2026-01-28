from minio import Minio
from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
import json
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class MinioClient:
    def __init__(self, retries=20, delay=5):
        self.client = Minio(
            config.MINIO_ENDPOINT,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=False,
        )
        self._ensure_buckets_with_retry(retries, delay)

    def _ensure_buckets_with_retry(self, retries, delay):
        for i in range(retries):
            try:
                if not self.client.bucket_exists(config.MINIO_BUCKET):
                    self.client.make_bucket(config.MINIO_BUCKET)
                if not self.client.bucket_exists(config.MINIO_AUDIO_BUCKET):
                    self.client.make_bucket(config.MINIO_AUDIO_BUCKET)
                print(f"✅ MinIO Connected (Attempt {i+1})")
                return
            except Exception as e:
                print(f"⚠️ MinIO Not Ready ({e}). Retry {i+1}...")
                time.sleep(delay)
        raise Exception("❌ MinIO Connection Failed!")

    # QUAN TRỌNG: Hàm này phải thụt đầu dòng ngang hàng với __init__
    def upload_file(
        self,
        file_path,
        object_name,
        bucket_name=config.MINIO_BUCKET,
        content_type="video/mp4",
    ):
        try:
            self.client.fput_object(
                bucket_name, object_name, file_path, content_type=content_type
            )
            # print(f"📤 Uploaded: {object_name}")
            return f"{bucket_name}/{object_name}"
        except Exception as e:
            print(f"❌ MinIO Upload Error: {e}")
            return None


class KafkaClient:
    def __init__(self, retries=20, delay=5):
        self._ensure_topic_with_retry(retries, delay)
        self.producer = None
        for i in range(retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                )
                print("✅ Kafka Producer Connected!")
                return
            except Exception as e:
                print(f"⚠️ Kafka Retry {i+1}: {e}")
                time.sleep(delay)
        raise Exception("❌ Kafka Connection Failed!")

    def _ensure_topic_with_retry(self, retries, delay):
        for i in range(retries):
            try:
                admin = KafkaAdminClient(
                    bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS
                )
                if config.KAFKA_TOPIC not in admin.list_topics():
                    admin.create_topics(
                        [
                            NewTopic(
                                name=config.KAFKA_TOPIC,
                                num_partitions=4,
                                replication_factor=1,
                            )
                        ]
                    )
                    print(f"✅ Topic '{config.KAFKA_TOPIC}' Created!")
                admin.close()
                return
            except Exception:
                time.sleep(delay)

    def send(self, data):
        try:
            self.producer.send(config.KAFKA_TOPIC, value=data)
            self.producer.flush()
            print(f"📡 Sent Kafka: {data.get('video_id')}")
        except Exception as e:
            print(f"❌ Kafka Send Error: {e}")
