# Real technical documentation

This directory is reserved for third-party technical documents used for
local evaluation.

Vendor manuals are intentionally not redistributed with this repository.
The application can be run immediately using the synthetic PDFs included
in `demo_docs/`.

## Siemens PLC manual used for portfolio evaluation

The real-document evaluation reported in this project used:

- **Document:** SIMATIC S7-1200 G2 Programmable Logic Controller System Manual
- **Version:** V4.1
- **Date:** 12/2025
- **Document ID:** A5E52923928-AC
- **Source:** Siemens Industry Online Support
- **Source URL:** https://support.industry.siemens.com/dl/files/791/109997791/att_1350879/v1/S71200_G2_system_manual_en-US_en-US.pdf
- **Accessed:** 29 September 2026
- **Expected filename:** `S71200_G2_system_manual_en-US_en-US.pdf`
- **Physical PDF pages:** 533
- **SHA-256:**
  `5c46f14aca74ed9387726c32b16ff2913a081160b442d760d0b22d05bb623ed6`

The Siemens manual is not redistributed with this repository. To reproduce
the real-document evaluation, download the manual from the source URL above
and place it in this directory:

```text
data/
└── S71200_G2_system_manual_en-US_en-US.pdf