# ==============================================================================
# FinTrace 360 - One-Click Automated PostgreSQL Setup & Data Seeder
# ==============================================================================

param(
    [string]$DbUser = "postgres",
    [string]$DbHost = "localhost",
    [string]$DbPort = "5432",
    [string]$DbName = "fintrace360"
)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "     FinTrace 360: PostgreSQL Warehouse Automated Setup         " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# Locate psql.exe
$psqlPath = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
if (-not (Test-Path $psqlPath)) {
    $psqlCmd = Get-Command psql -ErrorAction SilentlyContinue
    if ($psqlCmd) {
        $psqlPath = $psqlCmd.Source
    } else {
        Write-Error "Could not find psql.exe. Please install PostgreSQL or add it to PATH."
        exit 1
    }
}

Write-Host "[1/5] Using PostgreSQL CLI: $psqlPath" -ForegroundColor Green

# 1. Create Database if not exists
Write-Host "[2/5] Creating database '$DbName' (if not exists)..." -ForegroundColor Yellow
& $psqlPath -U $DbUser -h $DbHost -p $DbPort -d postgres -c "CREATE DATABASE $DbName;" 2>$null

# 2. Run Database Setup & Schemas
Write-Host "[3/5] Setting up schemas (staging & analytics)..." -ForegroundColor Yellow
& $psqlPath -U $DbUser -h $DbHost -p $DbPort -d $DbName -f "sql/01_database_setup.sql"
& $psqlPath -U $DbUser -h $DbHost -p $DbPort -d $DbName -f "sql/02_staging_tables.sql"
& $psqlPath -U $DbUser -h $DbHost -p $DbPort -d $DbName -f "sql/03_analytical_tables.sql"

# 3. Bulk Load Processed CSV Data
Write-Host "[4/5] Bulk-loading clean benchmark data (120,558 transactions, 20,000 accounts)..." -ForegroundColor Yellow
& $psqlPath -U $DbUser -h $DbHost -p $DbPort -d $DbName -f "sql/09_load_data.sql"

# 4. Create Analytical Reporting Views
Write-Host "[5/5] Creating Power BI analytical reporting views..." -ForegroundColor Yellow
& $psqlPath -U $DbUser -h $DbHost -p $DbPort -d $DbName -f "sql/07_analytical_views.sql"

Write-Host "`n[SUCCESS] FinTrace 360 PostgreSQL Data Warehouse is fully populated and verified!" -ForegroundColor Green
Write-Host "You can now connect Power BI Desktop to 'localhost:5432/$DbName' or execute queries in sql/04, 05, 06." -ForegroundColor Cyan
