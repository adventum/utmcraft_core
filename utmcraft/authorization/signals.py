from authorization.models import Profile


def create_user_profile(sender, instance, created, **kwargs):  # noqa
    if created:
        Profile.objects.create(user=instance)


def save_user_profile(sender, instance, **kwargs):  # noqa
    instance.profile.save()
