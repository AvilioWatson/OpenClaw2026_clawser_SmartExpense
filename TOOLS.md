# AGENT TOOLS DEFINITION

## 1. OCR Tool (`ocr_tool.py`)
- **Fungsi**: Ekstraksi teks dari gambar struk menggunakan EasyOCR.
- **Output**: Merchant, Date, Items (List), Total.

## 2. Calculator Tool (`calculator_tool.py`)
- **Fungsi**: Verifikasi matematis (Sum of items vs Total Tertera).
- **Self-Correction**: Melakukan loop hingga 3x jika ditemukan ketidakcocokan (Mismatch).

## 3. Budget Tool (`budget_tool.py`)
- **Fungsi**: Audit pengeluaran berdasarkan Personal Budget Rules.
- **Aturan**:
    - MAKANAN: Max Rp150.000/hari.
    - BARANG TERLARANG: Rokok, Vape, Alkohol (ATTENTION).
    - DUPLIKASI: Deteksi item ganda dalam satu struk.
