import os
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.


class WorkerArea(models.Model):
    """Modelo para área de trabajador (departamento o sección)."""

    name = models.CharField(max_length=100, unique=True, verbose_name=_('Name'), help_text=_("Name of the worker area"))
    description = models.TextField(blank=True, verbose_name=_('Description'), help_text=_("Description of the worker area"))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True, default=None)
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    updated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    def __str__(self):
        return self.name


class WorkShift(models.Model):
    """Modelo para controlar el turno de trabajo."""

    SHIFT_CHOICES = [
        ('morning', _('Morning')),
        ('afternoon', _('Afternoon')),
        ('night', _('Night')),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name=_('Name'), help_text=_("Name of the work shift"))
    start_time = models.TimeField(verbose_name=_('Start time'), help_text=_("Start time of the shift"))
    end_time = models.TimeField(verbose_name=_('End time'), help_text=_("End time of the shift"))
    shift_type = models.CharField(max_length=10, choices=SHIFT_CHOICES, verbose_name=_('Shift type'), help_text=_("Type of shift (morning, afternoon, night)"))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True, default=None)
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    updated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    def __str__(self):
        return self.name


class Profile(models.Model):
    """Modelo para el perfil de usuario."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    identity_document = models.CharField(max_length=15, null=True, blank=True, default=None)
    is_connected = models.BooleanField(default=True)
    bio = models.TextField(max_length=500, null=True, blank=True, default=None)
    location = models.CharField(max_length=30, null=True, blank=True, default=None)
    birth_date = models.DateField(null=True, blank=True, default=None)
    image = models.ImageField(default='images/profile_pics/avatar.png',
                              upload_to='uploads/profile_pics/')
    date_joined = models.DateField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True, default=None)
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    updated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    # New fields for WorkShift and WorkerArea
    work_shift = models.ForeignKey(WorkShift, null=True, blank=True, 
                                   on_delete=models.SET_NULL, 
                                   help_text=_("Assigned work shift"))
    worker_area = models.ForeignKey(WorkerArea, null=True, blank=True, 
                                    on_delete=models.SET_NULL, 
                                    help_text=_("Assigned worker area"))

    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(models.signals.post_delete, sender=Profile)
def trackfile_delete(sender, instance, **kwargs):
    """Auto-delete files from filesystem when they are unneeded.

    Deletes file from filesystem.
    when corresponding `SeguimientoArchivo` object is deleted.
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(models.signals.pre_save, sender=Profile)
def trackfile_delete_on_change(sender, instance, **kwargs):
    """Delete old file from filesystem.

    when corresponding `SeguimientoArchivo` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = Profile.objects.get(
            pk=instance.pk).image
    except Profile.DoesNotExist:
        return False

    new_file = instance.image
    if old_file:  # SI EL NOMBRE NO ES NULO
        if not old_file == new_file:
            if os.path.isfile(old_file.path):
                os.remove(old_file.path)


class EmotionAnalysis(models.Model):
    """Modelo para almacenar datos de análisis de emociones de los empleados durante los turnos de trabajo."""

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, help_text=_("The profile of the employee being analyzed"))
    # work_shift = models.ForeignKey(WorkShift, on_delete=models.CASCADE, help_text=_("The work shift during which the analysis is performed"))
    # video_file = models.FileField(upload_to='uploads/emotion_videos/', help_text=_("Video file of the employee during their shift"))
    video_file = models.FileField(upload_to='uploads/emotion_videos/', null=True, blank=True, help_text=_("Video file of the employee during their shift"))
    recorded_at = models.DateTimeField(default=timezone.now, help_text=_("Date and time when the video was recorded"))
    analyzed_at = models.DateTimeField(null=True, blank=True, help_text=_("Date and time when the video was analyzed"))
    emotions_detected = models.JSONField(null=True, blank=True, help_text=_("JSON field to store detected emotions and their probabilities"))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True, default=None)
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    updated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    # Método para obtener solo el nombre del archivo
    def video_filename(self):
        return self.video_file.name.split('/')[-1]

    def get_size(self):
        file_size = ''
        if self.video_file and hasattr(self.video_file, 'size'):
            file_size = self.video_file.size
        return file_size

    def get_filetype(self):
        filename = self.video_file.name
        return filename.split('.')[-1]

    # Sobrescribe el __str__ para mostrar el nombre del archivo
    def __str__(self):
        return f"{self.profile.user.username} - {self.video_filename()}"

    def delete(self, *args, **kwargs):
        if self.video_file:
            self.video_file.delete(save=False)  # Elimina el archivo físico
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.pk:  # Si el objeto ya existe (es una actualización)
            old_instance = EmotionAnalysis.objects.get(pk=self.pk)
            if old_instance.video_file and old_instance.video_file != self.video_file:
                old_instance.video_file.delete(save=False)  # Elimina el archivo anterior si se ha cambiado
        super().save(*args, **kwargs)
