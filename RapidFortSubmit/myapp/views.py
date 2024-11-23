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

@login_required
def upload(request):
    if request.method == 'POST' and request.FILES.get('doc_file'):
        doc_file = request.FILES['doc_file']
        fs = FileSystemStorage()
        file_name = fs.save(doc_file.name, doc_file)
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
import pythoncom
@login_required
def cvt(request, file_id, password=None):
    uploaded_file = UploadedFile.objects.get(id=file_id, user=request.user)

    if not uploaded_file or not os.path.exists(uploaded_file.uploaded_file_path):
        return render(request, 'error.html', {'message': 'File not found'})

    pdf_file_path = uploaded_file.uploaded_file_path.replace('.docx', '.pdf')

    try:
        pythoncom.CoInitialize()
        convert(uploaded_file.uploaded_file_path, pdf_file_path)
        if password:
            encrypt_pdf(pdf_file_path, password)

    finally:
        pythoncom.CoUninitialize()

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

from docx2pdf import convert
def generate_pdf(input_path, output_path, password=None):
    pythoncom.CoInitialize()  

    convert(input_path, output_path)

    if password:
        from PyPDF2 import PdfWriter, PdfReader
        with open(output_path, 'rb') as original_pdf:
            reader = PdfReader(original_pdf)
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)


            writer.encrypt(password)


            with open(output_path, 'wb') as encrypted_pdf:
                writer.write(encrypted_pdf)