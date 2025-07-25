"""Database router for multi-database setup in Coko project."""

class DatabaseRouter:
    """
    A router to control all database operations on models for different
    databases.
    """

    route_app_labels = {
        'auth_service': 'auth_db',
        'catalog_service': 'catalog_db', 
        'reading_service': 'reading_db',
        'recommendation_service': 'default',
        'payment_service': 'default',
        'gamification_service': 'default',
        'community_service': 'default',
        'admin_service': 'default',
        'notification_service': 'default',
    }

    def db_for_read(self, model, **hints):
        """Suggest the database to read from."""
        if model._meta.app_label in self.route_app_labels:
            return self.route_app_labels[model._meta.app_label]
        return None

    def db_for_write(self, model, **hints):
        """Suggest the database to write to."""
        if model._meta.app_label in self.route_app_labels:
            return self.route_app_labels[model._meta.app_label]
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the same app."""
        db_set = {'default', 'auth_db', 'catalog_db', 'reading_db'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that certain apps' models get created on the right database."""
        if app_label in self.route_app_labels:
            return db == self.route_app_labels[app_label]
        elif db in self.route_app_labels.values():
            return False
        return db == 'default'