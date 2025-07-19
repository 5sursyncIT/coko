# Système de gestion des langues africaines
# Implémente les recommandations pour le support multilingue

import json
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.core.cache import cache
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AfricanLanguageManager:
    """
    Gestionnaire des langues africaines avec support RTL et localisation
    """
    
    def __init__(self):
        # Langues africaines supportées avec leurs caractéristiques
        self.african_languages = {
            # Langues officielles principales
            'fr': {
                'name': 'Français',
                'native_name': 'Français',
                'code': 'fr',
                'iso_639_1': 'fr',
                'iso_639_2': 'fre',
                'direction': 'ltr',
                'countries': ['DZ', 'BJ', 'BF', 'BI', 'CM', 'CF', 'TD', 'KM', 'CG', 'CD', 'CI', 'DJ', 'GQ', 'GA', 'GN', 'MG', 'ML', 'MR', 'MA', 'NE', 'RW', 'SN', 'SC', 'TG', 'TN'],
                'speakers': 280000000,
                'literacy_rate': 0.65,
                'digital_presence': 'high',
                'font_family': 'system-ui, -apple-system, sans-serif',
                'keyboard_layout': 'azerty'
            },
            'en': {
                'name': 'English',
                'native_name': 'English',
                'code': 'en',
                'iso_639_1': 'en',
                'iso_639_2': 'eng',
                'direction': 'ltr',
                'countries': ['BW', 'CM', 'ET', 'GH', 'KE', 'LS', 'LR', 'MW', 'MU', 'NA', 'NG', 'RW', 'SC', 'SL', 'ZA', 'SS', 'SZ', 'TZ', 'UG', 'ZM', 'ZW'],
                'speakers': 237000000,
                'literacy_rate': 0.70,
                'digital_presence': 'high',
                'font_family': 'system-ui, -apple-system, sans-serif',
                'keyboard_layout': 'qwerty'
            },
            'ar': {
                'name': 'Arabic',
                'native_name': 'العربية',
                'code': 'ar',
                'iso_639_1': 'ar',
                'iso_639_2': 'ara',
                'direction': 'rtl',
                'countries': ['DZ', 'EG', 'LY', 'MA', 'SD', 'TN', 'TD', 'DJ', 'SO', 'ER'],
                'speakers': 422000000,
                'literacy_rate': 0.75,
                'digital_presence': 'high',
                'font_family': 'Noto Sans Arabic, Amiri, system-ui, sans-serif',
                'keyboard_layout': 'arabic'
            },
            'pt': {
                'name': 'Portuguese',
                'native_name': 'Português',
                'code': 'pt',
                'iso_639_1': 'pt',
                'iso_639_2': 'por',
                'direction': 'ltr',
                'countries': ['AO', 'CV', 'GW', 'MZ', 'ST', 'TL'],
                'speakers': 32000000,
                'literacy_rate': 0.60,
                'digital_presence': 'medium',
                'font_family': 'system-ui, -apple-system, sans-serif',
                'keyboard_layout': 'qwerty'
            },
            
            # Langues africaines principales
            'sw': {
                'name': 'Swahili',
                'native_name': 'Kiswahili',
                'code': 'sw',
                'iso_639_1': 'sw',
                'iso_639_2': 'swa',
                'direction': 'ltr',
                'countries': ['KE', 'TZ', 'UG', 'RW', 'BI', 'CD', 'MZ'],
                'speakers': 200000000,
                'literacy_rate': 0.55,
                'digital_presence': 'medium',
                'font_family': 'Noto Sans, system-ui, sans-serif',
                'keyboard_layout': 'qwerty'
            },
            'ha': {
                'name': 'Hausa',
                'native_name': 'Harshen Hausa',
                'code': 'ha',
                'iso_639_1': 'ha',
                'iso_639_2': 'hau',
                'direction': 'ltr',
                'countries': ['NG', 'NE', 'GH', 'CM', 'TD', 'SD'],
                'speakers': 70000000,
                'literacy_rate': 0.45,
                'digital_presence': 'low',
                'font_family': 'Noto Sans, system-ui, sans-serif',
                'keyboard_layout': 'qwerty'
            },
            'yo': {
                'name': 'Yoruba',
                'native_name': 'Èdè Yorùbá',
                'code': 'yo',
                'iso_639_1': 'yo',
                'iso_639_2': 'yor',
                'direction': 'ltr',
                'countries': ['NG', 'BJ', 'TG'],
                'speakers': 45000000,
                'literacy_rate': 0.40,
                'digital_presence': 'low',
                'font_family': 'Noto Sans, system-ui, sans-serif',
                'keyboard_layout': 'qwerty',
                'special_chars': ['ẹ', 'ọ', 'ṣ', 'ẹ́', 'ọ́', 'ṣ́']
            },
            'ig': {
                'name': 'Igbo',
                'native_name': 'Asụsụ Igbo',
                'code': 'ig',
                'iso_639_1': 'ig',
                'iso_639_2': 'ibo',
                'direction': 'ltr',
                'countries': ['NG'],
                'speakers': 27000000,
                'literacy_rate': 0.35,
                'digital_presence': 'low',
                'font_family': 'Noto Sans, system-ui, sans-serif',
                'keyboard_layout': 'qwerty',
                'special_chars': ['ị', 'ọ', 'ụ', 'ṅ', 'ṇ']
            },
            'am': {
                'name': 'Amharic',
                'native_name': 'አማርኛ',
                'code': 'am',
                'iso_639_1': 'am',
                'iso_639_2': 'amh',
                'direction': 'ltr',
                'countries': ['ET'],
                'speakers': 57000000,
                'literacy_rate': 0.50,
                'digital_presence': 'medium',
                'font_family': 'Noto Sans Ethiopic, system-ui, sans-serif',
                'keyboard_layout': 'ethiopic',
                'script': 'ethiopic'
            },
            'zu': {
                'name': 'Zulu',
                'native_name': 'isiZulu',
                'code': 'zu',
                'iso_639_1': 'zu',
                'iso_639_2': 'zul',
                'direction': 'ltr',
                'countries': ['ZA'],
                'speakers': 12000000,
                'literacy_rate': 0.65,
                'digital_presence': 'low',
                'font_family': 'Noto Sans, system-ui, sans-serif',
                'keyboard_layout': 'qwerty'
            },
            'xh': {
                'name': 'Xhosa',
                'native_name': 'isiXhosa',
                'code': 'xh',
                'iso_639_1': 'xh',
                'iso_639_2': 'xho',
                'direction': 'ltr',
                'countries': ['ZA'],
                'speakers': 8000000,
                'literacy_rate': 0.60,
                'digital_presence': 'low',
                'font_family': 'Noto Sans, system-ui, sans-serif',
                'keyboard_layout': 'qwerty'
            },
            'af': {
                'name': 'Afrikaans',
                'native_name': 'Afrikaans',
                'code': 'af',
                'iso_639_1': 'af',
                'iso_639_2': 'afr',
                'direction': 'ltr',
                'countries': ['ZA', 'NA'],
                'speakers': 7000000,
                'literacy_rate': 0.85,
                'digital_presence': 'medium',
                'font_family': 'system-ui, -apple-system, sans-serif',
                'keyboard_layout': 'qwerty'
            }
        }
        
        # Configuration des polices par script
        self.font_configs = {
            'latin': 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
            'arabic': '"Noto Sans Arabic", "Amiri", "Scheherazade", system-ui, sans-serif',
            'ethiopic': '"Noto Sans Ethiopic", "Abyssinica SIL", system-ui, sans-serif',
            'default': 'system-ui, -apple-system, sans-serif'
        }
    
    def get_user_language_preferences(self, request) -> Dict:
        """
        Détermine les préférences linguistiques de l'utilisateur
        """
        from .african_geolocation import get_user_location
        
        # Langue explicitement choisie
        chosen_lang = request.session.get('language')
        if chosen_lang and chosen_lang in self.african_languages:
            return self._get_language_config(chosen_lang)
        
        # Langue basée sur la géolocalisation
        location = get_user_location(request)
        country_code = location.get('country_code')
        
        if country_code:
            # Trouver les langues parlées dans ce pays
            country_languages = self._get_country_languages(country_code)
            if country_languages:
                # Prendre la langue la plus parlée
                primary_lang = max(country_languages, key=lambda x: self.african_languages[x]['speakers'])
                return self._get_language_config(primary_lang)
        
        # Langue basée sur Accept-Language
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        browser_langs = self._parse_accept_language(accept_language)
        
        for lang_code in browser_langs:
            if lang_code in self.african_languages:
                return self._get_language_config(lang_code)
        
        # Fallback vers le français (langue la plus parlée en Afrique)
        return self._get_language_config('fr')
    
    def _get_country_languages(self, country_code: str) -> List[str]:
        """
        Retourne les langues parlées dans un pays
        """
        languages = []
        for lang_code, lang_info in self.african_languages.items():
            if country_code in lang_info.get('countries', []):
                languages.append(lang_code)
        return languages
    
    def _parse_accept_language(self, accept_language: str) -> List[str]:
        """
        Parse l'en-tête Accept-Language
        """
        languages = []
        if accept_language:
            for lang in accept_language.split(','):
                lang_code = lang.split(';')[0].strip().lower()
                # Prendre seulement les 2 premiers caractères
                lang_code = lang_code[:2]
                if lang_code not in languages:
                    languages.append(lang_code)
        return languages
    
    def _get_language_config(self, lang_code: str) -> Dict:
        """
        Retourne la configuration complète d'une langue
        """
        if lang_code not in self.african_languages:
            lang_code = 'fr'  # Fallback
        
        lang_info = self.african_languages[lang_code]
        
        return {
            'code': lang_code,
            'name': lang_info['name'],
            'native_name': lang_info['native_name'],
            'direction': lang_info['direction'],
            'font_family': lang_info['font_family'],
            'keyboard_layout': lang_info.get('keyboard_layout', 'qwerty'),
            'special_chars': lang_info.get('special_chars', []),
            'script': lang_info.get('script', 'latin'),
            'digital_presence': lang_info['digital_presence'],
            'literacy_rate': lang_info['literacy_rate'],
            'is_rtl': lang_info['direction'] == 'rtl'
        }
    
    def get_available_languages(self, request=None) -> List[Dict]:
        """
        Retourne la liste des langues disponibles
        """
        languages = []
        
        for lang_code, lang_info in self.african_languages.items():
            languages.append({
                'code': lang_code,
                'name': lang_info['name'],
                'native_name': lang_info['native_name'],
                'direction': lang_info['direction'],
                'speakers': lang_info['speakers'],
                'digital_presence': lang_info['digital_presence']
            })
        
        # Trier par nombre de locuteurs
        languages.sort(key=lambda x: x['speakers'], reverse=True)
        
        return languages
    
    def get_language_css(self, lang_code: str) -> str:
        """
        Génère le CSS spécifique à une langue
        """
        config = self._get_language_config(lang_code)
        
        css = f"""
        /* CSS pour la langue {config['name']} ({lang_code}) */
        html[lang="{lang_code}"] {{
            direction: {config['direction']};
            font-family: {config['font_family']};
        }}
        
        html[lang="{lang_code}"] body {{
            text-align: {'right' if config['is_rtl'] else 'left'};
        }}
        
        /* Ajustements RTL */
        html[lang="{lang_code}"][dir="rtl"] .container {{
            direction: rtl;
        }}
        
        html[lang="{lang_code}"][dir="rtl"] .navbar-nav {{
            flex-direction: row-reverse;
        }}
        
        html[lang="{lang_code}"][dir="rtl"] .text-left {{
            text-align: right !important;
        }}
        
        html[lang="{lang_code}"][dir="rtl"] .text-right {{
            text-align: left !important;
        }}
        
        html[lang="{lang_code}"][dir="rtl"] .float-left {{
            float: right !important;
        }}
        
        html[lang="{lang_code}"][dir="rtl"] .float-right {{
            float: left !important;
        }}
        
        /* Polices spéciales pour certains scripts */
        """
        
        if config['script'] == 'arabic':
            css += f"""
        html[lang="{lang_code}"] {{
            font-feature-settings: "liga" 1, "calt" 1, "kern" 1;
            text-rendering: optimizeLegibility;
        }}
        
        html[lang="{lang_code}"] input, 
        html[lang="{lang_code}"] textarea {{
            font-family: {config['font_family']};
            direction: rtl;
        }}
        """
        
        elif config['script'] == 'ethiopic':
            css += f"""
        html[lang="{lang_code}"] {{
            line-height: 1.6;
            letter-spacing: 0.02em;
        }}
        """
        
        # Caractères spéciaux pour certaines langues
        if config.get('special_chars'):
            css += f"""
        html[lang="{lang_code}"] .special-chars {{
            font-variant-ligatures: common-ligatures;
        }}
        """
        
        return css
    
    def get_keyboard_layout(self, lang_code: str) -> Dict:
        """
        Retourne la configuration du clavier virtuel
        """
        config = self._get_language_config(lang_code)
        
        layouts = {
            'qwerty': {
                'type': 'qwerty',
                'special_keys': config.get('special_chars', []),
                'direction': config['direction']
            },
            'azerty': {
                'type': 'azerty',
                'special_keys': ['à', 'é', 'è', 'ç', 'ù'],
                'direction': 'ltr'
            },
            'arabic': {
                'type': 'arabic',
                'special_keys': ['ء', 'آ', 'أ', 'ؤ', 'إ', 'ئ'],
                'direction': 'rtl',
                'script': 'arabic'
            },
            'ethiopic': {
                'type': 'ethiopic',
                'special_keys': ['ሀ', 'ለ', 'ሐ', 'መ', 'ሠ', 'ረ'],
                'direction': 'ltr',
                'script': 'ethiopic'
            }
        }
        
        layout_type = config['keyboard_layout']
        return layouts.get(layout_type, layouts['qwerty'])
    
    def translate_content(self, content: str, target_lang: str, source_lang: str = 'auto') -> str:
        """
        Traduit du contenu (placeholder pour intégration future)
        """
        # Ici on intégrerait un service de traduction
        # comme Google Translate API ou un service local
        
        # Pour l'instant, retourner le contenu original
        return content
    
    def get_localization_data(self, lang_code: str) -> Dict:
        """
        Retourne les données de localisation pour une langue
        """
        config = self._get_language_config(lang_code)
        
        # Formats de date et nombre selon la région
        localization = {
            'date_format': self._get_date_format(lang_code),
            'time_format': self._get_time_format(lang_code),
            'number_format': self._get_number_format(lang_code),
            'currency_format': self._get_currency_format(lang_code),
            'first_day_of_week': self._get_first_day_of_week(lang_code),
            'reading_direction': config['direction'],
            'text_alignment': 'right' if config['is_rtl'] else 'left'
        }
        
        return localization
    
    def _get_date_format(self, lang_code: str) -> str:
        """
        Format de date selon la langue
        """
        formats = {
            'fr': 'DD/MM/YYYY',
            'en': 'MM/DD/YYYY',
            'ar': 'DD/MM/YYYY',
            'pt': 'DD/MM/YYYY',
            'am': 'DD/MM/YYYY'
        }
        return formats.get(lang_code, 'DD/MM/YYYY')
    
    def _get_time_format(self, lang_code: str) -> str:
        """
        Format d'heure selon la langue
        """
        formats = {
            'en': '12',  # 12 heures
            'ar': '12',
            'am': '12'
        }
        return formats.get(lang_code, '24')  # 24 heures par défaut
    
    def _get_number_format(self, lang_code: str) -> Dict:
        """
        Format des nombres selon la langue
        """
        formats = {
            'fr': {'decimal': ',', 'thousands': ' '},
            'en': {'decimal': '.', 'thousands': ','},
            'ar': {'decimal': '٫', 'thousands': '٬'},
            'pt': {'decimal': ',', 'thousands': '.'},
            'am': {'decimal': '.', 'thousands': ','}
        }
        return formats.get(lang_code, {'decimal': '.', 'thousands': ','})
    
    def _get_currency_format(self, lang_code: str) -> Dict:
        """
        Format des devises selon la langue
        """
        # Basé sur les principales devises africaines
        formats = {
            'fr': {'symbol': 'FCFA', 'position': 'after', 'space': True},
            'en': {'symbol': '$', 'position': 'before', 'space': False},
            'ar': {'symbol': 'د.ج', 'position': 'after', 'space': True},
            'pt': {'symbol': 'Kz', 'position': 'after', 'space': True}
        }
        return formats.get(lang_code, {'symbol': 'FCFA', 'position': 'after', 'space': True})
    
    def _get_first_day_of_week(self, lang_code: str) -> int:
        """
        Premier jour de la semaine (0 = dimanche, 1 = lundi)
        """
        # La plupart des pays africains commencent par lundi
        sunday_first = ['en']  # Certains pays anglophones
        return 0 if lang_code in sunday_first else 1


# Instance globale du gestionnaire de langues
language_manager = AfricanLanguageManager()


# Middleware pour la détection automatique de langue
class AfricanLanguageMiddleware:
    """
    Middleware pour la détection et configuration automatique de langue
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Détecter et configurer la langue
        lang_prefs = language_manager.get_user_language_preferences(request)
        lang_code = lang_prefs['code']
        
        # Activer la langue dans Django
        translation.activate(lang_code)
        request.LANGUAGE_CODE = lang_code
        request.LANGUAGE_CONFIG = lang_prefs
        
        # Ajouter les données de localisation
        request.LOCALIZATION_DATA = language_manager.get_localization_data(lang_code)
        
        response = self.get_response(request)
        
        # Ajouter les en-têtes de langue
        response['Content-Language'] = lang_code
        if lang_prefs['is_rtl']:
            response['X-Text-Direction'] = 'rtl'
        
        translation.deactivate()
        
        return response


# Vues Django pour la gestion des langues
def language_api_view(request):
    """
    API pour récupérer les informations de langue
    """
    if request.method == 'GET':
        # Retourner les langues disponibles
        languages = language_manager.get_available_languages(request)
        current_lang = language_manager.get_user_language_preferences(request)
        
        return JsonResponse({
            'current_language': current_lang,
            'available_languages': languages
        })
    
    elif request.method == 'POST':
        # Changer la langue
        import json
        data = json.loads(request.body)
        lang_code = data.get('language')
        
        if lang_code in language_manager.african_languages:
            request.session['language'] = lang_code
            translation.activate(lang_code)
            
            return JsonResponse({
                'status': 'success',
                'language': language_manager._get_language_config(lang_code)
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Langue non supportée'
            }, status=400)


def language_css_view(request, lang_code):
    """
    Vue pour servir le CSS spécifique à une langue
    """
    from django.http import HttpResponse
    
    css_content = language_manager.get_language_css(lang_code)
    
    response = HttpResponse(css_content, content_type='text/css')
    response['Cache-Control'] = 'public, max-age=86400'  # Cache 24h
    
    return response


def keyboard_layout_view(request, lang_code):
    """
    Vue pour récupérer la configuration du clavier
    """
    layout = language_manager.get_keyboard_layout(lang_code)
    
    return JsonResponse(layout)


# Fonctions utilitaires pour les templates
def get_language_direction(request):
    """
    Retourne la direction du texte pour la langue actuelle
    """
    return getattr(request, 'LANGUAGE_CONFIG', {}).get('direction', 'ltr')


def get_language_font_family(request):
    """
    Retourne la famille de police pour la langue actuelle
    """
    return getattr(request, 'LANGUAGE_CONFIG', {}).get('font_family', 'system-ui, sans-serif')


def is_rtl_language(request):
    """
    Vérifie si la langue actuelle est RTL
    """
    return getattr(request, 'LANGUAGE_CONFIG', {}).get('is_rtl', False)


def get_localized_number_format(request):
    """
    Retourne le format des nombres pour la langue actuelle
    """
    return getattr(request, 'LOCALIZATION_DATA', {}).get('number_format', {'decimal': '.', 'thousands': ','})


def format_african_currency(amount, currency_code, request):
    """
    Formate une devise selon les conventions africaines
    """
    localization = getattr(request, 'LOCALIZATION_DATA', {})
    currency_format = localization.get('currency_format', {'symbol': 'FCFA', 'position': 'after', 'space': True})
    number_format = localization.get('number_format', {'decimal': '.', 'thousands': ','})
    
    # Formater le nombre
    formatted_amount = f"{amount:,.2f}".replace(',', number_format['thousands']).replace('.', number_format['decimal'])
    
    # Ajouter le symbole de devise
    symbol = currency_format['symbol']
    space = ' ' if currency_format['space'] else ''
    
    if currency_format['position'] == 'before':
        return f"{symbol}{space}{formatted_amount}"
    else:
        return f"{formatted_amount}{space}{symbol}"


# Template tags personnalisés (à ajouter dans templatetags/)
def african_language_tags():
    """
    Template tags pour la gestion des langues africaines
    """
    from django import template
    
    register = template.Library()
    
    @register.simple_tag(takes_context=True)
    def language_direction(context):
        request = context['request']
        return get_language_direction(request)
    
    @register.simple_tag(takes_context=True)
    def language_font(context):
        request = context['request']
        return get_language_font_family(request)
    
    @register.simple_tag(takes_context=True)
    def is_rtl(context):
        request = context['request']
        return is_rtl_language(request)
    
    @register.filter
    def african_currency(value, currency_code='FCFA'):
        # Simplified version for template use
        return f"{value:,.2f} {currency_code}"
    
    return register