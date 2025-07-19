from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserPreferences, UserRole, Role
import re


class UserPreferencesSerializer(serializers.ModelSerializer):
    """Serializer pour les préférences utilisateur"""
    
    class Meta:
        model = UserPreferences
        exclude = ['user', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les informations utilisateur"""
    
    preferences = UserPreferencesSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    is_premium = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'avatar', 'country', 'language', 'subscription_type',
            'subscription_expires_at', 'is_verified', 'is_premium', 'preferences',
            'date_joined', 'last_login'
        ]
        read_only_fields = [
            'id', 'is_verified', 'subscription_type', 'subscription_expires_at',
            'date_joined', 'last_login'
        ]
    
    def validate_phone(self, value):
        """Validation du numéro de téléphone"""
        if value and not re.match(r'^\+?[1-9]\d{1,14}$', value):
            raise serializers.ValidationError("Format de téléphone invalide")
        return value


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription d'un nouvel utilisateur"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    terms_accepted = serializers.BooleanField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm', 'first_name',
            'last_name', 'phone', 'country', 'language', 'terms_accepted'
        ]
    
    def validate_email(self, value):
        """Validation de l'email"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Un compte avec cet email existe déjà")
        return value.lower()
    
    def validate_username(self, value):
        """Validation du nom d'utilisateur"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris")
        if len(value) < 3:
            raise serializers.ValidationError("Le nom d'utilisateur doit contenir au moins 3 caractères")
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError("Le nom d'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores")
        return value
    
    def validate_terms_accepted(self, value):
        """Validation de l'acceptation des conditions"""
        if not value:
            raise serializers.ValidationError("Vous devez accepter les conditions d'utilisation")
        return value
    
    def validate(self, attrs):
        """Validation croisée des mots de passe"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Les mots de passe ne correspondent pas"
            })
        return attrs
    
    def create(self, validated_data):
        """Création d'un nouvel utilisateur"""
        validated_data.pop('password_confirm')
        validated_data.pop('terms_accepted')
        
        user = User.objects.create_user(**validated_data)
        
        # Créer les préférences par défaut
        UserPreferences.objects.create(user=user)
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion utilisateur"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """Validation des identifiants de connexion"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email.lower(),
                password=password
            )
            
            if not user:
                raise serializers.ValidationError("Email ou mot de passe incorrect")
            
            if not user.is_active:
                raise serializers.ValidationError("Ce compte a été désactivé")
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError("Email et mot de passe requis")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personnalisé pour les tokens JWT"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Ajouter des claims personnalisés
        token['user_id'] = str(user.id)
        token['email'] = user.email
        token['subscription_type'] = user.subscription_type
        token['is_premium'] = user.is_premium
        token['country'] = user.country
        token['language'] = user.language
        
        return token


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer pour la demande de réinitialisation de mot de passe"""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validation de l'existence de l'email"""
        try:
            user = User.objects.get(email=value.lower())
            if not user.is_active:
                raise serializers.ValidationError("Ce compte a été désactivé")
        except User.DoesNotExist:
            # Pour des raisons de sécurité, on ne révèle pas si l'email existe
            pass
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer pour la confirmation de réinitialisation de mot de passe"""
    
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validation du token et des mots de passe"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Les mots de passe ne correspondent pas"
            })
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe"""
    
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_current_password(self, value):
        """Validation du mot de passe actuel"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe actuel incorrect")
        return value
    
    def validate(self, attrs):
        """Validation croisée des nouveaux mots de passe"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': "Les nouveaux mots de passe ne correspondent pas"
            })
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer pour la vérification d'email"""
    
    token = serializers.CharField()


class RoleSerializer(serializers.ModelSerializer):
    """Serializer pour les rôles"""
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions']
        read_only_fields = ['id']


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer pour les rôles utilisateur"""
    
    role = RoleSerializer(read_only=True)
    role_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'role', 'role_id', 'assigned_at']
        read_only_fields = ['id', 'assigned_at']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour du profil utilisateur"""
    
    preferences = UserPreferencesSerializer()
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'avatar', 'country', 
            'language', 'preferences'
        ]
    
    def update(self, instance, validated_data):
        """Mise à jour du profil avec les préférences"""
        preferences_data = validated_data.pop('preferences', None)
        
        # Mise à jour des informations utilisateur
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Mise à jour des préférences
        if preferences_data:
            preferences, created = UserPreferences.objects.get_or_create(user=instance)
            for attr, value in preferences_data.items():
                setattr(preferences, attr, value)
            preferences.save()
        
        return instance