@echo off
REM filepath: c:\Devs\python\agent_medical_ia\docker-scripts.bat

echo Docker Scripts pour Agent Medical IA
echo =====================================
echo.
echo 1. Demarrer les services
echo 2. Arreter les services
echo 3. Voir les logs
echo 4. Executer les migrations
echo 5. Creer un superuser
echo 6. Ouvrir shell Django
echo 7. Reconstruire les images
echo.
set /p choice=Choisissez une option (1-7): 

if "%choice%"=="1" (
    echo Demarrage des services...
    docker-compose up -d
) else if "%choice%"=="2" (
    echo Arret des services...
    docker-compose down
) else if "%choice%"=="3" (
    echo Affichage des logs...
    docker-compose logs -f
) else if "%choice%"=="4" (
    echo Execution des migrations...
    docker-compose exec web python manage.py migrate
) else if "%choice%"=="5" (
    echo Creation d'un superuser...
    docker-compose exec web python manage.py createsuperuser
) else if "%choice%"=="6" (
    echo Ouverture du shell Django...
    docker-compose exec web python manage.py shell
) else if "%choice%"=="7" (
    echo Reconstruction des images...
    docker-compose build --no-cache
) else (
    echo Option invalide
)

pause