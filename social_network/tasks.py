from celery import shared_task

from social_network.models import HashTag, Post, Profile


@shared_task
def create_scheduled_post(post_data: dict) -> None:
    """
    Create a new post instance with the provided data immediately
    when the task is executed.
    """
    post_data.pop("scheduled_at", None)
    author_id = post_data.pop("author_id")
    author = Profile.objects.get(pk=author_id)
    hashtag_captions = post_data.pop("hashtags", [])
    post = Post.objects.create(author=author, **post_data)

    hashtags = []
    for caption in hashtag_captions:
        hashtag, created = HashTag.objects.get_or_create(caption=caption)
        hashtags.append(hashtag)

    post.hashtags.set(hashtags)
