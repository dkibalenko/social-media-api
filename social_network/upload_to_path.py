import os
import uuid

from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_str
from django.utils.text import slugify


@deconstructible
class UploadToPath:
    """
    A callable class used to generate unique file paths for uploaded files.
    """
    def __init__(self, upload_to: str) -> None:
        self.upload_to = upload_to

    def __call__(self, instance: object, filename: str) -> str:
        return self.generate_upload_path(instance, filename)

    def get_directory_name(self) -> str:
        return os.path.normpath(force_str(self.upload_to))

    def get_filename(self, instance: object, filename: str) -> str:
        _, extension = os.path.splitext(filename)
        if hasattr(instance, "first_name") and hasattr(instance, "last_name"):
            slug_base = slugify(f"{instance.first_name}-{instance.last_name}")
        elif hasattr(instance, "title"):
            slug_base = slugify(instance.title)
        return f"{slug_base}-{uuid.uuid4()}{extension}"

    def generate_upload_path(self, instance: object, filename: str) -> str:
        return os.path.join(
            self.get_directory_name(), self.get_filename(instance, filename)
        )
