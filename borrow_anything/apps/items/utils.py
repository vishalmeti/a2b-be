# apps/items/utils.py

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging # Use logging instead of print for errors

logger = logging.getLogger(__name__) # Get a logger instance

def generate_s3_presigned_url(s3_key: str) -> str | None:
    """
    Generates a pre-signed URL for a given S3 object key.
    Reads configuration from Django settings.
    Returns the URL string or None if generation fails.
    """
    if not s3_key:
        return None

    # Retrieve AWS configuration from Django settings
    bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    region_name = getattr(settings, 'AWS_S3_REGION_NAME', None)
    expiration = getattr(settings, 'AWS_PRESIGNED_URL_EXPIRATION', 3600) # Default 1 hour

    if not bucket_name:
        logger.error("AWS_STORAGE_BUCKET_NAME not configured in settings.")
        return None

    # Create an S3 client instance
    # Ensure AWS credentials are configured (environment, ~/.aws/, IAM role)
    try:
        s3_client = boto3.client('s3', region_name=region_name)

        # Generate the pre-signed URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        logger.error(f"Could not generate pre-signed URL for key {s3_key}. ClientError: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during pre-signed URL generation for key {s3_key}: {e}")
        return None