# Instructions d'installation pour résoudre les problèmes de dépendances

## 🔧 SOLUTIONS POUR L'ERREUR WEASYPRINT/PYCAIRO

### Problème
L'erreur indique que `pycairo` ne peut pas être installé car il manque la bibliothèque système `cairo`.

### 🐳 SOLUTION 1: Docker (Recommandée)
```bash
# Utiliser Docker pour éviter les problèmes de dépendances système
docker-compose up --build

# Toutes les dépendances système sont gérées dans le Dockerfile
```

### 💻 SOLUTION 2: Installation Alternative (Sans WeasyPrint)
```bash
# Utiliser requirements-base.txt sans WeasyPrint
pip install -r requirements-base.txt

# Les exports PDF utiliseront ReportLab à la place
```

### 🖥️ SOLUTION 3: Installation des Dépendances Système

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libcairo2-dev \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info

# Puis installer les requirements Python
pip install -r requirements.txt
```

#### macOS:
```bash
# Installer via Homebrew
brew install cairo pango gdk-pixbuf libffi

# Puis installer les requirements Python
pip install -r requirements.txt
```

#### Windows:
```bash
# Installer GTK+ depuis:
# https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

# Ou utiliser conda
conda install -c conda-forge weasyprint

# Puis installer le reste
pip install -r requirements-base.txt
```

### 🔄 SOLUTION 4: Modification du Code pour ReportLab

Si vous utilisez `requirements-base.txt`, modifiez le code PDF:

```python
# Dans chat/api_views.py - remplacer WeasyPrint par ReportLab
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    WEASYPRINT_AVAILABLE = False

def export_pdf(self, request, pk=None):
    fiche = self.get_object()
    
    if WEASYPRINT_AVAILABLE:
        # Code WeasyPrint existant
        template = get_template('chat/fiche_pdf.html')
        html_content = template.render({'fiche': fiche})
        pdf_file = HTML(string=html_content).write_pdf()
    else:
        # Alternative ReportLab
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="consultation_{fiche.id}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Générer le contenu PDF avec ReportLab
        story.append(Paragraph(f"Consultation #{fiche.id}", styles['Title']))
        story.append(Paragraph(f"Patient: {fiche.user.get_full_name()}", styles['Normal']))
        # ... autres contenus
        
        doc.build(story)
        return response
```

### ✅ VERIFICATION DE L'INSTALLATION

```bash
# Tester l'installation
python manage.py shell

# Dans le shell Django:
try:
    from weasyprint import HTML
    print("✅ WeasyPrint disponible")
except ImportError:
    try:
        from reportlab.lib.pagesizes import letter
        print("✅ ReportLab disponible (alternative)")
    except ImportError:
        print("❌ Aucune solution PDF disponible")
```

### 🎯 RECOMMANDATION

**Pour le développement local:** Utilisez `requirements-base.txt` avec ReportLab  
**Pour la production:** Utilisez Docker avec WeasyPrint complet

Le projet fonctionnera dans les deux cas, seule la qualité de rendu PDF sera légèrement différente.