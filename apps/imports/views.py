from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import ImportBatch
from .forms import ImportBatchForm
from .tasks import process_import_batch_task

def is_reviewer(user):
    return user.role in ['ADMIN', 'REVIEWER']

@login_required
@user_passes_test(is_reviewer)
def upload_csv(request):
    if request.method == 'POST':
        form = ImportBatchForm(request.POST, request.FILES)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.uploaded_by = request.user
            batch.filename = request.FILES['file'].name
            batch.save()
            
            # Running synchronously for now (no .delay)
            process_import_batch_task(batch.id) 
            
            messages.success(request, "File uploaded and processed successfully.")
            return redirect('imports:import_summary', pk=batch.pk)
    else:
        form = ImportBatchForm()
        
    return render(request, 'imports/upload.html', {'form': form})

@login_required
def import_summary(request, pk):
    batch = get_object_or_404(ImportBatch, pk=pk)
    return render(request, 'imports/summary.html', {'batch': batch})