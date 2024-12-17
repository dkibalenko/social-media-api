import os
import uuid

from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_str
from django.utils.text import slugify


@deconstructible
class UploadToPath:
    def __init__(self, upload_to: str) -> None:
        self.upload_to = upload_to

    def __call__(self, instance: object, filename: str) -> str:
        return self.generate_upload_path(instance, filename)

    def get_directory_name(self) -> str:
        return os.path.normpath(force_str(self.upload_to))

    def get_filename(self, instance: object, filename: str) -> str:
        _, extension = os.path.splitext(filename)
        return f"{slugify(f'{instance.first_name}-{instance.last_name}')}-\
            {uuid.uuid4()}{extension}"

    def generate_upload_path(self, instance: object, filename: str) -> str:
        return os.path.join(
            self.get_directory_name(), self.get_filename(instance, filename)
        )
