from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import FileResponse
from .models import UploadedFile, ConversionHistory
import os
from PyPDF2 import PdfWriter, PdfReader

def homePage(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')

import re

def sanitize_filename(filename):
    return re.sub(r'[^\w\s.-]', '_', filename)

@login_required
def upload(request):
    if request.method == 'POST' and request.FILES.get('doc_file'):
        doc_file = request.FILES['doc_file']
        sanitized_name = sanitize_filename(doc_file.name)
        fs = FileSystemStorage()
        file_name = fs.save(sanitized_name, doc_file)
        file_path = fs.path(file_name)
        encrypt_pdf = request.POST.get('encrypt_pdf')
        password = request.POST.get('password') if encrypt_pdf else None
        uploaded_file = UploadedFile.objects.create(
            user=request.user,
            original_file_name=doc_file.name,
            uploaded_file_path=file_path,
            converted_file_path=file_path.replace('.docx', '.pdf'),
        )
        return redirect('convert', file_id=uploaded_file.id, password=password)
    
    return render(request, 'upload.html')
import logging

@login_required
def cvt(request, file_id, password=None):
    uploaded_file = UploadedFile.objects.get(id=file_id, user=request.user)

    if not uploaded_file or not os.path.exists(uploaded_file.uploaded_file_path):
        return render(request, 'error.html', {'message': 'File not found'})

    pdf_file_path = uploaded_file.uploaded_file_path.replace('.docx', '.pdf')

    try:
        # Convert DOCX to PDF
        generate_pdf(uploaded_file.uploaded_file_path, pdf_file_path, password)

        # Confirm the PDF exists
        if not os.path.exists(pdf_file_path):
            logging.error(f"PDF file not created: {pdf_file_path}")
            return render(request, 'error.html', {'message': 'PDF conversion failed'})

    except subprocess.CalledProcessError as e:
        logging.error(f"LibreOffice error: {str(e)}")
        return render(request, 'error.html', {'message': f'Conversion error: {str(e)}'})

    ConversionHistory.objects.create(
        user=request.user,
        original_file_name=uploaded_file.original_file_name,
        converted_file_path=pdf_file_path,
    )

    return redirect('download', file_id=uploaded_file.id)

def encrypt_pdf(pdf_file_path, password):
    reader = PdfReader(pdf_file_path)
    writer = PdfWriter()

    # Add all pages from the reader
    for page in reader.pages:
        writer.add_page(page)

    # Encrypt the PDF with the password
    writer.encrypt(password)

    # Write the encrypted PDF to the file
    with open(pdf_file_path, 'wb') as output_pdf:
        writer.write(output_pdf)



@login_required
def download(request, file_id):
    try:
        uploaded_file = UploadedFile.objects.get(id=file_id, user=request.user)
    except UploadedFile.DoesNotExist:
        return render(request, 'error.html', {'message': 'File not found'})
    
    if not uploaded_file.converted_file_path or not os.path.exists(uploaded_file.converted_file_path):
        return render(request, 'error.html', {'message': 'PDF not found'})

    return FileResponse(open(uploaded_file.converted_file_path, 'rb'), as_attachment=True, filename=os.path.basename(uploaded_file.converted_file_path))

@login_required
def history(request):
    # Retrieve conversion history for the current user
    history = ConversionHistory.objects.filter(user=request.user).order_by('-uploaded_at')

    return render(request, 'history.html', {'history': history})

import subprocess

def generate_pdf(input_path, output_path, password=None):
    command = [
        "soffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        os.path.dirname(output_path),
        input_path,
    ]
    result = subprocess.run(command, check=True)
    if os.path.exists(output_path):
        print(f"PDF created successfully: {output_path}")
    else:
        print(f"PDF creation failed: {output_path}")
    if password:
        encrypt_pdf(output_path, password)
