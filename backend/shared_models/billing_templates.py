"""Templates et générateurs de documents pour le système de facturation Coko"""

from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
import os
import logging
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service pour la génération et l'envoi d'emails de facturation"""
    
    @staticmethod
    def send_invoice_email(invoice, recipient_email=None):
        """Envoie un email de facture"""
        try:
            recipient = recipient_email or invoice.billing_email or invoice.user.email
            
            # Contexte pour le template
            context = {
                'invoice': invoice,
                'user': invoice.user,
                'company_name': getattr(settings, 'COMPANY_NAME', 'Coko'),
                'company_email': getattr(settings, 'COMPANY_EMAIL', 'contact@coko.com'),
                'company_phone': getattr(settings, 'COMPANY_PHONE', '+33 1 23 45 67 89'),
                'company_address': getattr(settings, 'COMPANY_ADDRESS', '123 Rue de la Paix, 75001 Paris'),
                'base_url': getattr(settings, 'BASE_URL', 'https://coko.com'),
                'current_year': timezone.now().year
            }
            
            # Génération du contenu HTML
            html_content = render_to_string('billing/invoice_email.html', context)
            text_content = render_to_string('billing/invoice_email.txt', context)
            
            # Sujet de l'email
            subject = f"Facture {invoice.invoice_number} - {context['company_name']}"
            
            # Création de l'email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=context['company_email'],
                to=[recipient]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Génération et attachement du PDF
            pdf_content = PDFInvoiceGenerator.generate_invoice_pdf(invoice)
            email.attach(
                f"facture_{invoice.invoice_number}.pdf",
                pdf_content,
                'application/pdf'
            )
            
            # Envoi
            email.send()
            
            logger.info(f"Email de facture envoyé pour {invoice.invoice_number} à {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de facture {invoice.invoice_number}: {str(e)}")
            return False
    
    @staticmethod
    def send_royalty_notification(author, royalties, total_amount):
        """Envoie une notification de royalties à un auteur"""
        try:
            context = {
                'author': author,
                'royalties': royalties,
                'total_amount': total_amount,
                'currency': royalties[0].currency if royalties else 'EUR',
                'period_start': min(r.period_start for r in royalties),
                'period_end': max(r.period_end for r in royalties),
                'company_name': getattr(settings, 'COMPANY_NAME', 'Coko'),
                'company_email': getattr(settings, 'COMPANY_EMAIL', 'contact@coko.com'),
                'base_url': getattr(settings, 'BASE_URL', 'https://coko.com'),
                'current_year': timezone.now().year
            }
            
            html_content = render_to_string('billing/royalty_notification.html', context)
            text_content = render_to_string('billing/royalty_notification.txt', context)
            
            subject = f"Notification de royalties - {context['company_name']}"
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=context['company_email'],
                to=[author.email]
            )
            email.attach_alternative(html_content, "text/html")
            
            email.send()
            
            logger.info(f"Notification de royalties envoyée à {author.email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification de royalties à {author.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_overdue_notification(invoice):
        """Envoie une notification de retard de paiement"""
        try:
            recipient = invoice.billing_email or invoice.user.email
            
            context = {
                'invoice': invoice,
                'user': invoice.user,
                'days_overdue': invoice.days_overdue,
                'company_name': getattr(settings, 'COMPANY_NAME', 'Coko'),
                'company_email': getattr(settings, 'COMPANY_EMAIL', 'contact@coko.com'),
                'company_phone': getattr(settings, 'COMPANY_PHONE', '+33 1 23 45 67 89'),
                'base_url': getattr(settings, 'BASE_URL', 'https://coko.com'),
                'current_year': timezone.now().year
            }
            
            html_content = render_to_string('billing/overdue_notification.html', context)
            text_content = render_to_string('billing/overdue_notification.txt', context)
            
            subject = f"Rappel de paiement - Facture {invoice.invoice_number}"
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=context['company_email'],
                to=[recipient]
            )
            email.attach_alternative(html_content, "text/html")
            
            email.send()
            
            logger.info(f"Notification de retard envoyée pour {invoice.invoice_number} à {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification de retard {invoice.invoice_number}: {str(e)}")
            return False


class PDFInvoiceGenerator:
    """Générateur de factures PDF"""
    
    @staticmethod
    def generate_invoice_pdf(invoice):
        """Génère un PDF de facture"""
        buffer = BytesIO()
        
        # Configuration du document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # Contenu du document
        story = []
        
        # En-tête de l'entreprise
        company_name = getattr(settings, 'COMPANY_NAME', 'Coko')
        story.append(Paragraph(f"<b>{company_name}</b>", title_style))
        
        company_info = [
            getattr(settings, 'COMPANY_ADDRESS', '123 Rue de la Paix, 75001 Paris'),
            f"Tél: {getattr(settings, 'COMPANY_PHONE', '+33 1 23 45 67 89')}",
            f"Email: {getattr(settings, 'COMPANY_EMAIL', 'contact@coko.com')}"
        ]
        
        for info in company_info:
            story.append(Paragraph(info, normal_style))
        
        story.append(Spacer(1, 20))
        
        # Informations de facturation
        billing_data = [
            ['Facture N°:', invoice.invoice_number],
            ['Date d\'émission:', invoice.issue_date.strftime('%d/%m/%Y')],
            ['Date d\'échéance:', invoice.due_date.strftime('%d/%m/%Y')],
            ['Statut:', invoice.get_status_display()]
        ]
        
        if invoice.paid_date:
            billing_data.append(['Date de paiement:', invoice.paid_date.strftime('%d/%m/%Y')])
        
        billing_table = Table(billing_data, colWidths=[2*inch, 2*inch])
        billing_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(billing_table)
        story.append(Spacer(1, 20))
        
        # Informations client
        story.append(Paragraph("<b>Facturé à:</b>", header_style))
        
        client_info = [
            invoice.billing_name or invoice.user.get_full_name(),
            invoice.billing_email or invoice.user.email
        ]
        
        if invoice.billing_address:
            client_info.append(invoice.billing_address)
        
        if invoice.billing_phone:
            client_info.append(f"Tél: {invoice.billing_phone}")
        
        for info in client_info:
            story.append(Paragraph(info, normal_style))
        
        story.append(Spacer(1, 20))
        
        # Détails de la facture
        story.append(Paragraph("<b>Détails de la facture:</b>", header_style))
        
        # En-têtes du tableau
        items_data = [[
            'Description',
            'Quantité',
            'Prix unitaire',
            'Total'
        ]]
        
        # Lignes de facture
        for item in invoice.items.all():
            items_data.append([
                item.description,
                str(item.quantity),
                f"{item.unit_price} {invoice.currency}",
                f"{item.total_amount} {invoice.currency}"
            ])
        
        # Tableau des articles
        items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Totaux
        totals_data = []
        
        if invoice.discount_amount and invoice.discount_amount > 0:
            totals_data.append(['Sous-total:', f"{invoice.subtotal} {invoice.currency}"])
            totals_data.append(['Remise:', f"-{invoice.discount_amount} {invoice.currency}"])
        
        if invoice.tax_amount and invoice.tax_amount > 0:
            totals_data.append(['TVA:', f"{invoice.tax_amount} {invoice.currency}"])
        
        totals_data.append(['<b>Total:</b>', f"<b>{invoice.total_amount} {invoice.currency}</b>"])
        
        totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(totals_table)
        story.append(Spacer(1, 30))
        
        # Notes
        if invoice.notes:
            story.append(Paragraph("<b>Notes:</b>", header_style))
            story.append(Paragraph(invoice.notes, normal_style))
            story.append(Spacer(1, 20))
        
        # Conditions de paiement
        payment_terms = [
            "Conditions de paiement:",
            "• Paiement dû dans les 30 jours suivant la date d'émission",
            "• Pénalités de retard applicables après la date d'échéance",
            "• Pour toute question, contactez-nous à l'adresse indiquée ci-dessus"
        ]
        
        for term in payment_terms:
            if term.startswith('•'):
                story.append(Paragraph(term, normal_style))
            else:
                story.append(Paragraph(f"<b>{term}</b>", header_style))
        
        # Génération du PDF
        doc.build(story)
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    @staticmethod
    def generate_royalty_report_pdf(author, royalties, period_start, period_end):
        """Génère un rapport PDF de royalties pour un auteur"""
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        )
        
        story = []
        
        # Titre
        story.append(Paragraph("Rapport de Royalties", title_style))
        
        # Informations auteur
        author_info = [
            ['Auteur:', author.get_full_name()],
            ['Email:', author.email],
            ['Période:', f"{period_start.strftime('%d/%m/%Y')} - {period_end.strftime('%d/%m/%Y')}"],
            ['Date du rapport:', timezone.now().strftime('%d/%m/%Y')]
        ]
        
        author_table = Table(author_info, colWidths=[2*inch, 4*inch])
        author_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(author_table)
        story.append(Spacer(1, 20))
        
        # Détails des royalties
        royalties_data = [[
            'Livre',
            'Type',
            'Montant base',
            'Taux',
            'Royalty'
        ]]
        
        total_royalties = Decimal('0')
        currency = 'EUR'
        
        for royalty in royalties:
            currency = royalty.currency
            total_royalties += royalty.royalty_amount
            
            royalties_data.append([
                royalty.book_title or 'N/A',
                royalty.get_royalty_type_display(),
                f"{royalty.base_amount} {royalty.currency}",
                f"{float(royalty.royalty_rate * 100):.1f}%",
                f"{royalty.royalty_amount} {royalty.currency}"
            ])
        
        royalties_table = Table(royalties_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        royalties_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(royalties_table)
        story.append(Spacer(1, 20))
        
        # Total
        total_data = [['<b>Total des royalties:</b>', f"<b>{total_royalties} {currency}</b>"]]
        total_table = Table(total_data, colWidths=[4*inch, 2*inch])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(total_table)
        
        doc.build(story)
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content


class BillingReportGenerator:
    """Générateur de rapports de facturation"""
    
    @staticmethod
    def generate_monthly_billing_report(year, month):
        """Génère un rapport mensuel de facturation"""
        from .billing import Invoice, AuthorRoyalty
        from django.db.models import Sum, Count, Q
        
        # Période
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Statistiques des factures
        invoices_stats = Invoice.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        ).aggregate(
            total_count=Count('id'),
            total_amount=Sum('total_amount'),
            paid_count=Count('id', filter=Q(status='paid')),
            paid_amount=Sum('total_amount', filter=Q(status='paid')),
            overdue_count=Count('id', filter=Q(status='overdue')),
            overdue_amount=Sum('total_amount', filter=Q(status='overdue'))
        )
        
        # Statistiques des royalties
        royalties_stats = AuthorRoyalty.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        ).aggregate(
            total_count=Count('id'),
            total_amount=Sum('royalty_amount'),
            paid_count=Count('id', filter=Q(status='paid')),
            paid_amount=Sum('royalty_amount', filter=Q(status='paid'))
        )
        
        return {
            'period': f"{month:02d}/{year}",
            'invoices': invoices_stats,
            'royalties': royalties_stats,
            'generated_at': timezone.now()
        }


# Templates HTML pour les emails (à créer dans templates/billing/)
INVOICE_EMAIL_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Facture {{ invoice.invoice_number }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .invoice-details { background-color: #f8f9fa; padding: 15px; margin: 20px 0; }
        .footer { background-color: #34495e; color: white; padding: 15px; text-align: center; }
        .button { background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ company_name }}</h1>
        <p>Facture {{ invoice.invoice_number }}</p>
    </div>
    
    <div class="content">
        <p>Bonjour {{ user.get_full_name }},</p>
        
        <p>Veuillez trouver ci-joint votre facture {{ invoice.invoice_number }} d'un montant de {{ invoice.total_amount }} {{ invoice.currency }}.</p>
        
        <div class="invoice-details">
            <h3>Détails de la facture</h3>
            <p><strong>Numéro:</strong> {{ invoice.invoice_number }}</p>
            <p><strong>Date d'émission:</strong> {{ invoice.issue_date|date:"d/m/Y" }}</p>
            <p><strong>Date d'échéance:</strong> {{ invoice.due_date|date:"d/m/Y" }}</p>
            <p><strong>Montant:</strong> {{ invoice.total_amount }} {{ invoice.currency }}</p>
            <p><strong>Statut:</strong> {{ invoice.get_status_display }}</p>
        </div>
        
        {% if invoice.status != 'paid' %}
        <p>Le paiement est dû avant le {{ invoice.due_date|date:"d/m/Y" }}.</p>
        <p><a href="{{ base_url }}/billing/pay/{{ invoice.id }}" class="button">Payer maintenant</a></p>
        {% endif %}
        
        <p>Pour toute question concernant cette facture, n'hésitez pas à nous contacter.</p>
    </div>
    
    <div class="footer">
        <p>{{ company_name }} - {{ company_email }} - {{ company_phone }}</p>
        <p>{{ company_address }}</p>
    </div>
</body>
</html>
"""

INVOICE_EMAIL_TEXT_TEMPLATE = """
Bonjour {{ user.get_full_name }},

Veuillez trouver ci-joint votre facture {{ invoice.invoice_number }} d'un montant de {{ invoice.total_amount }} {{ invoice.currency }}.

Détails de la facture:
- Numéro: {{ invoice.invoice_number }}
- Date d'émission: {{ invoice.issue_date|date:"d/m/Y" }}
- Date d'échéance: {{ invoice.due_date|date:"d/m/Y" }}
- Montant: {{ invoice.total_amount }} {{ invoice.currency }}
- Statut: {{ invoice.get_status_display }}

{% if invoice.status != 'paid' %}
Le paiement est dû avant le {{ invoice.due_date|date:"d/m/Y" }}.
Vous pouvez payer en ligne: {{ base_url }}/billing/pay/{{ invoice.id }}
{% endif %}

Pour toute question concernant cette facture, n'hésitez pas à nous contacter.

Cordialement,
{{ company_name }}
{{ company_email }}
{{ company_phone }}
{{ company_address }}
"""