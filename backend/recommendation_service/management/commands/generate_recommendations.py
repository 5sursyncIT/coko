from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
import logging
from typing import Optional, List

from recommendation_service.models import UserProfile, RecommendationSet
from recommendation_service.utils import generate_personalized_recommendations
from recommendation_service.tasks import (
    generate_user_recommendations, batch_generate_recommendations
)

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Générer des recommandations personnalisées pour les utilisateurs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID de l\'utilisateur spécifique pour lequel générer des recommandations'
        )
        
        parser.add_argument(
            '--username',
            type=str,
            help='Nom d\'utilisateur spécifique pour lequel générer des recommandations'
        )
        
        parser.add_argument(
            '--algorithm',
            type=str,
            choices=['content_based', 'collaborative', 'popularity', 'hybrid'],
            default='hybrid',
            help='Algorithme de recommandation à utiliser (défaut: hybrid)'
        )
        
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Nombre de recommandations à générer par utilisateur (défaut: 10)'
        )
        
        parser.add_argument(
            '--context',
            type=str,
            default='general',
            help='Contexte des recommandations (défaut: general)'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Taille des lots pour le traitement en masse (défaut: 50)'
        )
        
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Générer des recommandations pour tous les utilisateurs actifs'
        )
        
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Générer uniquement pour les utilisateurs avec recommandations activées'
        )
        
        parser.add_argument(
            '--async',
            action='store_true',
            dest='use_async',
            help='Utiliser les tâches asynchrones (Celery) pour la génération'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la génération même si des recommandations récentes existent'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans réellement générer les recommandations'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé des opérations'
        )
    
    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        
        try:
            if options['user_id'] or options['username']:
                self._handle_single_user(options)
            elif options['all_users']:
                self._handle_all_users(options)
            else:
                raise CommandError(
                    "Vous devez spécifier --user-id, --username ou --all-users"
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération de recommandations: {str(e)}")
            raise CommandError(f"Erreur: {str(e)}")
    
    def _handle_single_user(self, options):
        """Gérer la génération pour un utilisateur spécifique"""
        user = self._get_user(options)
        
        if not user:
            raise CommandError("Utilisateur non trouvé")
        
        self._log(f"Génération de recommandations pour l'utilisateur: {user.username}")
        
        if options['dry_run']:
            self._log("[DRY RUN] Simulation de génération")
            return
        
        if not self._should_generate_recommendations(user, options['force']):
            self._log("Recommandations récentes trouvées, génération ignorée (utilisez --force pour forcer)")
            return
        
        if options['use_async']:
            self._generate_async_single(user, options)
        else:
            self._generate_sync_single(user, options)
    
    def _handle_all_users(self, options):
        """Gérer la génération pour tous les utilisateurs"""
        users_query = User.objects.filter(is_active=True)
        
        if options['active_only']:
            users_query = users_query.filter(
                userprofile__enable_recommendations=True
            )
        
        users = list(users_query.select_related('userprofile'))
        
        if not users:
            self._log("Aucun utilisateur trouvé")
            return
        
        self._log(f"Génération de recommandations pour {len(users)} utilisateurs")
        
        if options['dry_run']:
            self._log("[DRY RUN] Simulation de génération pour tous les utilisateurs")
            return
        
        # Filtrer les utilisateurs qui ont besoin de nouvelles recommandations
        if not options['force']:
            users = [u for u in users if self._should_generate_recommendations(u, False)]
            self._log(f"Après filtrage: {len(users)} utilisateurs nécessitent de nouvelles recommandations")
        
        if options['use_async']:
            self._generate_async_batch(users, options)
        else:
            self._generate_sync_batch(users, options)
    
    def _get_user(self, options) -> Optional[User]:
        """Obtenir l'utilisateur à partir des options"""
        if options['user_id']:
            try:
                return User.objects.get(id=options['user_id'])
            except User.DoesNotExist:
                return None
        
        if options['username']:
            try:
                return User.objects.get(username=options['username'])
            except User.DoesNotExist:
                return None
        
        return None
    
    def _should_generate_recommendations(self, user: User, force: bool) -> bool:
        """Vérifier si des recommandations doivent être générées pour cet utilisateur"""
        if force:
            return True
        
        # Vérifier s'il y a des recommandations récentes (moins de 24h)
        recent_threshold = timezone.now() - timezone.timedelta(hours=24)
        recent_recommendations = RecommendationSet.objects.filter(
            user=user,
            created_at__gte=recent_threshold
        ).exists()
        
        return not recent_recommendations
    
    def _generate_sync_single(self, user: User, options):
        """Générer des recommandations de manière synchrone pour un utilisateur"""
        try:
            with transaction.atomic():
                recommendations = generate_personalized_recommendations(
                    user=user,
                    algorithm=options['algorithm'],
                    count=options['count'],
                    context=options['context']
                )
                
                if recommendations:
                    self._log(f"✓ {len(recommendations)} recommandations générées pour {user.username}")
                else:
                    self._log(f"⚠ Aucune recommandation générée pour {user.username}")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la génération pour {user.username}: {str(e)}")
            self._log(f"✗ Erreur pour {user.username}: {str(e)}")
    
    def _generate_sync_batch(self, users: List[User], options):
        """Générer des recommandations de manière synchrone pour plusieurs utilisateurs"""
        batch_size = options['batch_size']
        total_users = len(users)
        successful = 0
        failed = 0
        
        for i in range(0, total_users, batch_size):
            batch = users[i:i + batch_size]
            self._log(f"Traitement du lot {i//batch_size + 1}/{(total_users-1)//batch_size + 1}")
            
            for user in batch:
                try:
                    with transaction.atomic():
                        recommendations = generate_personalized_recommendations(
                            user=user,
                            algorithm=options['algorithm'],
                            count=options['count'],
                            context=options['context']
                        )
                        
                        if recommendations:
                            successful += 1
                            if self.verbose:
                                self._log(f"  ✓ {user.username}: {len(recommendations)} recommandations")
                        else:
                            if self.verbose:
                                self._log(f"  ⚠ {user.username}: aucune recommandation")
                                
                except Exception as e:
                    failed += 1
                    logger.error(f"Erreur pour {user.username}: {str(e)}")
                    if self.verbose:
                        self._log(f"  ✗ {user.username}: {str(e)}")
        
        self._log(f"Terminé: {successful} succès, {failed} échecs")
    
    def _generate_async_single(self, user: User, options):
        """Générer des recommandations de manière asynchrone pour un utilisateur"""
        try:
            task = generate_user_recommendations.delay(
                user_id=user.id,
                algorithm=options['algorithm'],
                count=options['count'],
                context=options['context']
            )
            
            self._log(f"Tâche asynchrone lancée pour {user.username}: {task.id}")
            
        except Exception as e:
            logger.error(f"Erreur lors du lancement de la tâche pour {user.username}: {str(e)}")
            self._log(f"✗ Erreur pour {user.username}: {str(e)}")
    
    def _generate_async_batch(self, users: List[User], options):
        """Générer des recommandations de manière asynchrone pour plusieurs utilisateurs"""
        user_ids = [user.id for user in users]
        
        try:
            result = batch_generate_recommendations.delay(
                user_ids=user_ids,
                algorithm=options['algorithm']
            )
            
            self._log(f"Tâche de génération en lot lancée: {result.id}")
            self._log(f"Utilisateurs en file d'attente: {len(user_ids)}")
            
        except Exception as e:
            logger.error(f"Erreur lors du lancement de la tâche en lot: {str(e)}")
            self._log(f"✗ Erreur lors du lancement: {str(e)}")
    
    def _log(self, message: str):
        """Logger un message selon le niveau de verbosité"""
        if self.verbosity >= 1:
            self.stdout.write(message)
        
        logger.info(message)
    
    def _log_success(self, message: str):
        """Logger un message de succès"""
        if self.verbosity >= 1:
            self.stdout.write(self.style.SUCCESS(message))
        
        logger.info(message)
    
    def _log_warning(self, message: str):
        """Logger un message d'avertissement"""
        if self.verbosity >= 1:
            self.stdout.write(self.style.WARNING(message))
        
        logger.warning(message)
    
    def _log_error(self, message: str):
        """Logger un message d'erreur"""
        if self.verbosity >= 1:
            self.stdout.write(self.style.ERROR(message))
        
        logger.error(message)