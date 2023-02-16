from client_admin.models import ClientAdmin


def create_client_admin(sender, instance, created, **kwargs):  # noqa
    if created:
        ClientAdmin.objects.create(user=instance)


def save_client_admin(sender, instance, **kwargs):  # noqa
    instance.clientadmin.save()
