from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from django.utils.text import slugify
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import logging
import os

from .models import (
    Book, Author, Publisher, Category, Series, BookFile, 
    BookRating, BookTag, BookTagAssignment, BookCollection
)

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Book)
def book_pre_save(sender, instance, **kwargs):
    """Signal avant sauvegarde d'un livre"""
    # Générer le slug automatiquement si pas défini
    if not instance.slug:
        instance.slug = slugify(instance.title)
        
        # Vérifier l'unicité du slug
        original_slug = instance.slug
        counter = 1
        while Book.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1
    
    # Définir la date de publication si le statut passe à 'published'
    if instance.status == 'published' and not instance.published_at:
        from django.utils import timezone
        instance.published_at = timezone.now()


@receiver(post_save, sender=Book)
def book_post_save(sender, instance, created, **kwargs):
    """Signal après sauvegarde d'un livre"""
    # Invalider le cache des statistiques
    cache.delete('book_stats')
    
    if created:
        logger.info(f"Nouveau livre créé: {instance.title} (ID: {instance.id})")
        
        # Envoyer une notification aux administrateurs pour les nouveaux livres
        if hasattr(settings, 'ADMIN_EMAIL') and settings.ADMIN_EMAIL:
            try:
                subject = f"Nouveau livre ajouté: {instance.title}"
                message = render_to_string('catalog/emails/new_book_notification.html', {
                    'book': instance,
                    'admin_url': f"{settings.ADMIN_URL}/catalog/book/{instance.id}/change/"
                })
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    html_message=message,
                    fail_silently=True
                )
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de notification pour le nouveau livre: {e}")
    else:
        logger.info(f"Livre modifié: {instance.title} (ID: {instance.id})")
        
        # Si le livre devient publié, notifier les auteurs
        if instance.status == 'published':
            try:
                for author in instance.authors.all():
                    if hasattr(author, 'user') and author.user and author.user.email:
                        subject = f"Votre livre '{instance.title}' a été publié"
                        message = render_to_string('catalog/emails/book_published.html', {
                            'book': instance,
                            'author': author
                        })
                        
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[author.user.email],
                            html_message=message,
                            fail_silently=True
                        )
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de notification de publication: {e}")


@receiver(post_delete, sender=Book)
def book_post_delete(sender, instance, **kwargs):
    """Signal après suppression d'un livre"""
    # Invalider le cache des statistiques
    cache.delete('book_stats')
    
    # Supprimer les fichiers associés
    if instance.cover_image:
        try:
            if os.path.isfile(instance.cover_image.path):
                os.remove(instance.cover_image.path)
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'image de couverture: {e}")
    
    logger.info(f"Livre supprimé: {instance.title} (ID: {instance.id})")


@receiver(pre_save, sender=Author)
def author_pre_save(sender, instance, **kwargs):
    """Signal avant sauvegarde d'un auteur"""
    if not instance.slug:
        instance.slug = slugify(f"{instance.first_name}-{instance.last_name}")
        
        # Vérifier l'unicité du slug
        original_slug = instance.slug
        counter = 1
        while Author.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1


@receiver(post_save, sender=Author)
def author_post_save(sender, instance, created, **kwargs):
    """Signal après sauvegarde d'un auteur"""
    if created:
        logger.info(f"Nouvel auteur créé: {instance.full_name} (ID: {instance.id})")
    else:
        logger.info(f"Auteur modifié: {instance.full_name} (ID: {instance.id})")


@receiver(post_delete, sender=Author)
def author_post_delete(sender, instance, **kwargs):
    """Signal après suppression d'un auteur"""
    # Supprimer la photo si elle existe
    if instance.photo:
        try:
            if os.path.isfile(instance.photo.path):
                os.remove(instance.photo.path)
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la photo de l'auteur: {e}")
    
    logger.info(f"Auteur supprimé: {instance.full_name} (ID: {instance.id})")


@receiver(pre_save, sender=Publisher)
def publisher_pre_save(sender, instance, **kwargs):
    """Signal avant sauvegarde d'un éditeur"""
    if not instance.slug:
        instance.slug = slugify(instance.name)
        
        # Vérifier l'unicité du slug
        original_slug = instance.slug
        counter = 1
        while Publisher.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1


@receiver(post_save, sender=Publisher)
def publisher_post_save(sender, instance, created, **kwargs):
    """Signal après sauvegarde d'un éditeur"""
    if created:
        logger.info(f"Nouvel éditeur créé: {instance.name} (ID: {instance.id})")
    else:
        logger.info(f"Éditeur modifié: {instance.name} (ID: {instance.id})")


@receiver(post_delete, sender=Publisher)
def publisher_post_delete(sender, instance, **kwargs):
    """Signal après suppression d'un éditeur"""
    # Supprimer le logo si il existe
    if instance.logo:
        try:
            if os.path.isfile(instance.logo.path):
                os.remove(instance.logo.path)
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du logo de l'éditeur: {e}")
    
    logger.info(f"Éditeur supprimé: {instance.name} (ID: {instance.id})")


@receiver(pre_save, sender=Category)
def category_pre_save(sender, instance, **kwargs):
    """Signal avant sauvegarde d'une catégorie"""
    if not instance.slug:
        instance.slug = slugify(instance.name)
        
        # Vérifier l'unicité du slug
        original_slug = instance.slug
        counter = 1
        while Category.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1


@receiver(post_save, sender=Category)
def category_post_save(sender, instance, created, **kwargs):
    """Signal après sauvegarde d'une catégorie"""
    if created:
        logger.info(f"Nouvelle catégorie créée: {instance.name} (ID: {instance.id})")
    else:
        logger.info(f"Catégorie modifiée: {instance.name} (ID: {instance.id})")


@receiver(pre_save, sender=Series)
def series_pre_save(sender, instance, **kwargs):
    """Signal avant sauvegarde d'une série"""
    if not instance.slug:
        instance.slug = slugify(instance.title)
        
        # Vérifier l'unicité du slug
        original_slug = instance.slug
        counter = 1
        while Series.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1


@receiver(post_save, sender=Series)
def series_post_save(sender, instance, created, **kwargs):
    """Signal après sauvegarde d'une série"""
    if created:
        logger.info(f"Nouvelle série créée: {instance.title} (ID: {instance.id})")
    else:
        logger.info(f"Série modifiée: {instance.title} (ID: {instance.id})")


@receiver(post_save, sender=BookFile)
def book_file_post_save(sender, instance, created, **kwargs):
    """Signal après sauvegarde d'un fichier de livre"""
    if created:
        logger.info(f"Nouveau fichier ajouté pour le livre {instance.book.title}: {instance.format}")
        
        # Mettre à jour la taille du fichier si pas définie
        if not instance.file_size and instance.file:
            try:
                instance.file_size = instance.file.size
                instance.save(update_fields=['file_size'])
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour de la taille du fichier: {e}")


@receiver(post_delete, sender=BookFile)
def book_file_post_delete(sender, instance, **kwargs):
    """Signal après suppression d'un fichier de livre"""
    # Supprimer le fichier physique
    if instance.file:
        try:
            if os.path.isfile(instance.file.path):
                os.remove(instance.file.path)
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du fichier: {e}")
    
    logger.info(f"Fichier supprimé pour le livre {instance.book.title}: {instance.format}")


@receiver(post_save, sender=BookRating)
def book_rating_post_save(sender, instance, created, **kwargs):
    """Signal après sauvegarde d'une évaluation"""
    # Invalider le cache des statistiques
    cache.delete('book_stats')
    
    if created:
        logger.info(f"Nouvelle évaluation pour {instance.book.title} par {instance.user.username}: {instance.score}/5")
        
        # Notifier l'auteur de la nouvelle évaluation (si configuré)
        try:
            if hasattr(settings, 'NOTIFY_AUTHORS_ON_RATING') and settings.NOTIFY_AUTHORS_ON_RATING:
                for author in instance.book.authors.all():
                    if hasattr(author, 'user') and author.user and author.user.email:
                        subject = f"Nouvelle évaluation pour votre livre '{instance.book.title}'"
                        message = render_to_string('catalog/emails/new_rating.html', {
                            'book': instance.book,
                            'rating': instance,
                            'author': author
                        })
                        
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[author.user.email],
                            html_message=message,
                            fail_silently=True
                        )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification d'évaluation: {e}")


@receiver(post_delete, sender=BookRating)
def book_rating_post_delete(sender, instance, **kwargs):
    """Signal après suppression d'une évaluation"""
    # Invalider le cache des statistiques
    cache.delete('book_stats')
    
    logger.info(f"Évaluation supprimée pour {instance.book.title} par {instance.user.username}")


@receiver(pre_save, sender=BookTag)
def book_tag_pre_save(sender, instance, **kwargs):
    """Signal avant sauvegarde d'un tag"""
    if not instance.slug:
        instance.slug = slugify(instance.name)
        
        # Vérifier l'unicité du slug
        original_slug = instance.slug
        counter = 1
        while BookTag.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1


@receiver(post_save, sender=BookTag)
def book_tag_post_save(sender, instance, created, **kwargs):
    """Signal après sauvegarde d'un tag"""
    if created:
        logger.info(f"Nouveau tag créé: {instance.name} (ID: {instance.id})")


@receiver(pre_save, sender=BookCollection)
def book_collection_pre_save(sender, instance, **kwargs):
    """Signal avant sauvegarde d'une collection"""
    if not instance.slug:
        instance.slug = slugify(instance.title)
        
        # Vérifier l'unicité du slug
        original_slug = instance.slug
        counter = 1
        while BookCollection.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1


@receiver(post_save, sender=BookCollection)
def book_collection_post_save(sender, instance, created, **kwargs):
    """Signal après sauvegarde d'une collection"""
    if created:
        logger.info(f"Nouvelle collection créée: {instance.title} par {instance.created_by.username}")
    else:
        logger.info(f"Collection modifiée: {instance.title} par {instance.created_by.username}")