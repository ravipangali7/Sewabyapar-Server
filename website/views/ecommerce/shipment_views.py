from django.shortcuts import render, get_object_or_404, HttpResponse
from django.conf import settings
from django.core.exceptions import ValidationError
from ecommerce.models import Order, Store
from website.models import MySetting
import requests
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import os


def shipment_documents_view(request, store_id, order_id):
    """Public view to display shipment documents download page"""
    try:
        # Get settings for template
        try:
            site_settings = MySetting.objects.first()
        except:
            site_settings = None
        
        # Validate store exists
        store = get_object_or_404(Store, id=store_id, is_active=True)
        
        # Validate order exists and belongs to the store
        order = get_object_or_404(Order, id=order_id, merchant=store)
        
        # Check if shipment files exist
        has_label = bool(order.shipdaak_label_url)
        has_manifest = bool(order.shipdaak_manifest_url)
        
        if not has_label and not has_manifest:
            context = {
                'settings': site_settings,
                'error': 'No shipment documents available for this order.',
                'order_number': order.order_number,
            }
            return render(request, 'website/ecommerce/shipment_documents.html', context, status=404)
        
        context = {
            'settings': site_settings,
            'store': store,
            'order': order,
            'has_label': has_label,
            'has_manifest': has_manifest,
            'order_number': order.order_number,
        }
        
        return render(request, 'website/ecommerce/shipment_documents.html', context)
        
    except Store.DoesNotExist:
        try:
            site_settings = MySetting.objects.first()
        except:
            site_settings = None
        context = {
            'settings': site_settings,
            'error': 'Invalid order. Store not found.',
        }
        return render(request, 'website/ecommerce/shipment_documents.html', context, status=404)
    except Order.DoesNotExist:
        try:
            site_settings = MySetting.objects.first()
        except:
            site_settings = None
        context = {
            'settings': site_settings,
            'error': 'Invalid order. Order not found or does not belong to this store.',
        }
        return render(request, 'website/ecommerce/shipment_documents.html', context, status=404)
    except Exception as e:
        try:
            site_settings = MySetting.objects.first()
        except:
            site_settings = None
        context = {
            'settings': site_settings,
            'error': f'An error occurred: {str(e)}',
        }
        return render(request, 'website/ecommerce/shipment_documents.html', context, status=500)


def _add_logo_to_label_pdf(pdf_url, logo_path):
    """
    Download PDF from URL, add logo at top-right, and return PDF bytes
    Logo positioned at top-right corner, max 100px width
    """
    try:
        # Download original PDF
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Read original PDF
        original_pdf = PdfReader(io.BytesIO(response.content))
        pdf_writer = PdfWriter()
        
        # Load logo image
        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"Logo file not found: {logo_path}")
        
        logo_img = Image.open(logo_path)
        
        # Process each page
        for page_num, page in enumerate(original_pdf.pages):
            # Get page dimensions
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            # Create a new PDF page with logo
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(page_width, page_height))
            
            # Calculate logo size (max 100px width, maintain aspect ratio)
            logo_width = min(100, page_width * 0.15)
            logo_aspect = logo_img.height / logo_img.width
            logo_height = logo_width * logo_aspect
            
            # Position logo at top-right (with some margin)
            x_position = page_width - logo_width - 20
            y_position = page_height - logo_height - 20
            
            # Draw logo (fully opaque, 100% opacity)
            can.drawImage(
                ImageReader(logo_img),
                x_position,
                y_position,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )
            
            can.save()
            
            # Move to the beginning of the StringIO buffer
            packet.seek(0)
            logo_pdf = PdfReader(packet)
            
            # Merge logo page with original page
            page.merge_page(logo_pdf.pages[0])
            
            # Add merged page to writer
            pdf_writer.add_page(page)
        
        # Write merged PDF to bytes
        output = io.BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        return output.getvalue()
        
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")


def _add_logo_to_manifest_pdf(pdf_url, logo_path):
    """
    Download PDF from URL, add logo at top-left (smaller size), and return PDF bytes
    Logo positioned at top-left, smaller size (max 60px), typically above Courier area
    """
    try:
        # Download original PDF
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Read original PDF
        original_pdf = PdfReader(io.BytesIO(response.content))
        pdf_writer = PdfWriter()
        
        # Load logo image
        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"Logo file not found: {logo_path}")
        
        logo_img = Image.open(logo_path)
        
        # Process each page
        for page_num, page in enumerate(original_pdf.pages):
            # Get page dimensions
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            # Create a new PDF page with logo
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(page_width, page_height))
            
            # Calculate logo size (max 60px width, smaller than label, maintain aspect ratio)
            logo_width = min(60, page_width * 0.10)
            logo_aspect = logo_img.height / logo_img.width
            logo_height = logo_width * logo_aspect
            
            # Position logo at top-left (with some margin, above Courier area)
            # Increased gap from top to position logo lower (more downside)
            x_position = 45
            y_position = page_height - logo_height - 60
            
            # Draw logo (fully opaque, 100% opacity)
            can.drawImage(
                ImageReader(logo_img),
                x_position,
                y_position,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )
            
            can.save()
            
            # Move to the beginning of the StringIO buffer
            packet.seek(0)
            logo_pdf = PdfReader(packet)
            
            # Merge logo page with original page
            page.merge_page(logo_pdf.pages[0])
            
            # Add merged page to writer
            pdf_writer.add_page(page)
        
        # Write merged PDF to bytes
        output = io.BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        return output.getvalue()
        
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")


def download_shipment_label(request, store_id, order_id):
    """Download shipment label PDF with logo"""
    try:
        # Validate store and order
        store = get_object_or_404(Store, id=store_id, is_active=True)
        order = get_object_or_404(Order, id=order_id, merchant=store)
        
        if not order.shipdaak_label_url:
            return HttpResponse("Label not available for this order.", status=404)
        
        # Get logo path
        logo_path = os.path.join(settings.STATIC_ROOT, 'logo.png')
        
        # Add logo to PDF (top-right position)
        pdf_bytes = _add_logo_to_label_pdf(order.shipdaak_label_url, logo_path)
        
        # Create response
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="label_order_{order.order_number}.pdf"'
        
        return response
        
    except Exception as e:
        return HttpResponse(f"Error downloading label: {str(e)}", status=500)


def download_shipment_manifest(request, store_id, order_id):
    """Download shipment manifest PDF with logo"""
    try:
        # Validate store and order
        store = get_object_or_404(Store, id=store_id, is_active=True)
        order = get_object_or_404(Order, id=order_id, merchant=store)
        
        if not order.shipdaak_manifest_url:
            return HttpResponse("Manifest not available for this order.", status=404)
        
        # Get logo path
        logo_path = os.path.join(settings.STATIC_ROOT, 'logo.png')
        
        # Add logo to PDF (top-left position, smaller size)
        pdf_bytes = _add_logo_to_manifest_pdf(order.shipdaak_manifest_url, logo_path)
        
        # Create response
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="manifest_order_{order.order_number}.pdf"'
        
        return response
        
    except Exception as e:
        return HttpResponse(f"Error downloading manifest: {str(e)}", status=500)
