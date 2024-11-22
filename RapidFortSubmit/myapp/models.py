from django.db import models
from django.contrib.auth.models import User


class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_file_name = models.CharField(max_length=255)
    uploaded_file_path = models.TextField()
    converted_file_path = models.TextField()
    upload_date = models.DateTimeField(auto_now_add=True)


class ConversionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_file_name = models.CharField(max_length=255)
    converted_file_path = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.original_file_name} converted on {self.uploaded_at}'