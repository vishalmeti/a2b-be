import boto3
from django.conf import settings
from botocore.config import Config

class S3ImageUploader:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            # config=Config(signature_version='s3v4'),
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME


    def upload_image(self, file, s3_key):
        """Upload an image to S3."""
        try:
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': file.content_type}
            )
            return self.get_image_presigned_url(s3_key)
        except Exception as e:
            raise Exception(f"Error uploading image to S3: {str(e)}")
    def delete_image(self, s3_key):
        """Delete an image from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
        except Exception as e:
            raise Exception(f"Error deleting image from S3: {str(e)}")
    def get_image_presigned_url(self, s3_key):
        """Get the URL of an image stored in S3."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=60 * 60 * 24  # URL valid for 24 hours
            )
            return url
        except Exception as e:
            raise Exception(f"Error generating image URL: {str(e)}")
    def get_image_metadata(self, s3_key):
        """Get metadata of an image stored in S3."""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return {
                'ContentType': response['ContentType'],
                'LastModified': response['LastModified'],
                'Size': response['ContentLength']
            }
        except Exception as e:
            raise Exception(f"Error retrieving image metadata: {str(e)}")

