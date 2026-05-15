# AGENT MEMORY: User Financial Goals

## Context Schema
Agen menyimpan memori berupa "Goals" atau target finansial user di dalam database SQLite.

## Memory Template
- **Goal Text**: Apa yang ingin dibeli/dicapai user (misal: "Beli Sepatu Nike").
- **Timestamp**: Kapan target ini dibuat.
- **User ID**: ID Telegram unik user.

## Retrieval Strategy
Setiap kali audit dilakukan, agen akan mengambil `latest_goal` dari user tersebut untuk dijadikan konteks dalam memberikan nasihat/omelan.
